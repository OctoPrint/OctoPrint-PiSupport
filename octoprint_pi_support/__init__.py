__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2017 The OctoPrint Project - Released under terms of the AGPLv3 License"

import os
from getpass import getuser

import flask
import octoprint.events
import octoprint.plugin
import sarge
from flask_babel import gettext
from octoprint.access.groups import USER_GROUP
from octoprint.access.permissions import Permissions
from octoprint.util import RepeatedTimer
from octoprint.util.platform import CLOSE_FDS

_PROC_DT_MODEL_PATH = "/proc/device-tree/model"
_OCTOPI_VERSION_PATH = "/etc/octopi_version"
_OCTOPIUPTODATE_BUILD_PATH = "/etc/octopiuptodate_build"
_NEW_CAMERA_STACK_PATH = "/etc/systemd/system/camera-streamer-usb@.service"
_VCGENCMD_THROTTLE = "/usr/bin/vcgencmd get_throttled"
_SSHWARN_PATH = "/run/sshwarn"

_CHECK_INTERVAL_OK = 300
_CHECK_INTERVAL_THROTTLED = 30


def _gather_new_camerastack_files():
    import logging

    files = {}

    try:
        os.system(
            "journalctl --boot -u 'camera-streamer*' > /tmp/camerastack-journal.log"
        )
        files["camerastack-journal.log"] = "/tmp/camerastack-journal.log"
    except Exception:
        logging.getLogger(__name__).exception(
            "Failed to create camerastack-journal.log file"
        )

    try:
        os.system(
            "/usr/bin/libcamera-hello --list-cameras > /tmp/camerastack-libcamera.log"
        )
        files["camerastack-libcamera.log"] = "/tmp/camerastack-libcamera.log"
    except Exception:
        logging.getLogger(__name__).exception(
            "Failed to create camerastack-libcamera.log file"
        )

    try:
        os.system("/usr/bin/list-usb-cameras > /tmp/camerastack-usb.log")
        files["camerastack-usb.log"] = "/tmp/camerastack-usb.log"
    except Exception:
        logging.getLogger(__name__).exception("Failed to create camerastack-usb.log file")

    return files


__LOCAL_DEBUG = os.path.exists(
    os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".local_debug"))
)

if __LOCAL_DEBUG:
    ### mocks & settings for local debugging
    base = os.path.realpath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "tests",
            "fakes",
        )
    )
    debug = os.path.realpath(
        os.path.join(os.path.dirname(__file__), "..", ".local_debug")
    )
    _PROC_DT_MODEL_PATH = os.path.join(base, "fake_model.txt")
    _OCTOPI_VERSION_PATH = os.path.join(base, "fake_octopi.txt")
    _OCTOPIUPTODATE_BUILD_PATH = os.path.join(base, "fake_octopiuptodate.txt")
    _NEW_CAMERA_STACK_PATH = os.path.join(debug, "new-camera-stack")
    _SSHWARN_PATH = os.path.join(debug, "sshwarn")

    _gather_new_camerastack_files = lambda: {  # noqa: F811
        "camerastack-journal.log": os.path.join(base, "fake_camerastack_journal.txt"),
        "camerastack-libcamera.log": os.path.join(base, "fake_camerastack_libcamera.txt"),
        "camerastack-usb.log": os.path.join(base, "fake_camerastack_usb.txt"),
    }

    import itertools

    _VCGENCMD_OUTPUT = itertools.chain(
        iter(("0x0", "0x0", "0x50005", "0x50000", "0x70007")),
        itertools.repeat("0x70005"),
    )
    _VCGENCMD_BROKEN = os.path.exists(os.path.join(debug, "vcgencmd_broken"))

    _CHECK_INTERVAL_OK = 10
    _CHECK_INTERVAL_THROTTLED = 5


# see https://www.raspberrypi.org/forums/viewtopic.php?f=63&t=147781&start=50#p972790
_FLAG_UNDERVOLTAGE = 1 << 0
_FLAG_FREQ_CAPPED = 1 << 1
_FLAG_THROTTLED = 1 << 2
_FLAG_PAST_UNDERVOLTAGE = 1 << 16
_FLAG_PAST_FREQ_CAPPED = 1 << 17
_FLAG_PAST_THROTTLED = 1 << 18

_UNRECOMMENDED_MODELS = ("Zero", "Zero W")


class ThrottleState:
    @classmethod
    def from_value(cls, value=0):
        if value == 0:
            return ThrottleState(raw_value=value)

        kwargs = {
            "undervoltage": _FLAG_UNDERVOLTAGE & value == _FLAG_UNDERVOLTAGE,
            "freq_capped": _FLAG_FREQ_CAPPED & value == _FLAG_FREQ_CAPPED,
            "throttled": _FLAG_THROTTLED & value == _FLAG_THROTTLED,
            "past_undervoltage": _FLAG_PAST_UNDERVOLTAGE & value
            == _FLAG_PAST_UNDERVOLTAGE,
            "past_freq_capped": _FLAG_PAST_FREQ_CAPPED & value == _FLAG_PAST_FREQ_CAPPED,
            "past_throttled": _FLAG_PAST_THROTTLED & value == _FLAG_PAST_THROTTLED,
            "raw_value": value,
        }
        return ThrottleState(**kwargs)

    def __init__(self, **kwargs):
        self._raw_value = kwargs.get("raw_value", -1)
        self._undervoltage = False
        self._freq_capped = False
        self._throttled = False
        self._past_undervoltage = False
        self._past_freq_capped = False
        self._past_throttled = False

        for key, value in kwargs.items():
            local_key = f"_{key}"
            if hasattr(self, local_key) and isinstance(value, bool):
                setattr(self, local_key, value)

    @property
    def undervoltage(self):
        return self.current_undervoltage or self.past_undervoltage

    @property
    def current_undervoltage(self):
        return self._undervoltage

    @property
    def past_undervoltage(self):
        return self._past_undervoltage

    @property
    def overheat(self):
        return self.current_overheat or self.past_overheat

    @property
    def current_overheat(self):
        return self._freq_capped

    @property
    def past_overheat(self):
        return self._past_freq_capped

    @property
    def issue(self):
        return self.current_issue or self.past_issue

    @property
    def current_issue(self):
        return self._undervoltage or self._freq_capped or self._throttled

    @property
    def past_issue(self):
        return self._past_undervoltage or self._past_freq_capped or self._past_throttled

    @property
    def raw_value(self):
        return self._raw_value

    @property
    def raw_value_hex(self):
        return f"0x{self._raw_value:X}"

    def __eq__(self, other):
        if not isinstance(other, ThrottleState):
            return False

        return (
            self._undervoltage == other._undervoltage
            and self._freq_capped == other._freq_capped
            and self._throttled == other._throttled
            and self._past_undervoltage == other._past_undervoltage
            and self._past_freq_capped == other._past_freq_capped
            and self._past_throttled == other._past_throttled
            and self._raw_value == other._raw_value
        )

    def as_dict(self):
        return {
            "raw_value": self._raw_value,
            "current_undervoltage": self.current_undervoltage,
            "past_undervoltage": self.past_undervoltage,
            "current_overheat": self.current_overheat,
            "past_overheat": self.past_overheat,
            "current_issue": self.current_issue,
            "past_issue": self.past_issue,
        }


_proc_dt_model = None


def get_proc_dt_model():
    global _proc_dt_model

    if _proc_dt_model is None:
        with open(_PROC_DT_MODEL_PATH, encoding="utf-8") as f:
            _proc_dt_model = f.readline().strip(" \t\r\n\0")

    return _proc_dt_model


def get_vcgencmd_throttled_state(command):
    if __LOCAL_DEBUG:
        if _VCGENCMD_BROKEN:
            output = ""
            error = "VCHI initialization failed"
        else:
            output = "throttled={}".format(
                next(_VCGENCMD_OUTPUT)
            )  # mock for local debugging
            error = ""
    else:
        output, error = sarge.get_both(command, close_fds=CLOSE_FDS)

    if "throttled=0x" not in output:
        raise ValueError(f"Cannot parse {command!r} output: {error if error else output}")

    value = output[len("throttled=") :].strip(" \t\r\n\0")
    value = int(value, 0)
    return ThrottleState.from_value(value)


def is_octopi():
    return os.path.exists(_OCTOPI_VERSION_PATH)


def is_octopiuptodate():
    return os.path.exists(_OCTOPIUPTODATE_BUILD_PATH)


def is_new_camerastack():
    return os.path.exists(_NEW_CAMERA_STACK_PATH)


def is_model_any_of(model, *args):
    model = model.lower()
    for arg in (x.lower() for x in args):
        if f"{arg} rev" in model or model.endswith(arg):
            return True
    return False


_octopi_version = None


def get_octopi_version():
    global _octopi_version

    if _octopi_version is None:
        with open(_OCTOPI_VERSION_PATH, encoding="utf-8") as f:
            _octopi_version = f.readline().strip(" \t\r\n\0")

    return _octopi_version


_octopiuptodate_build = None


def get_octopiuptodate_build():
    global _octopiuptodate_build

    if _octopiuptodate_build is None:
        with open(_OCTOPIUPTODATE_BUILD_PATH, encoding="utf-8") as f:
            _octopiuptodate_build = f.readline().strip(" \t\r\n\0")

    return _octopiuptodate_build


def has_default_password():
    # It would be nicer to actually fetch the hash from /etc/shadow here and verify it
    # has been changed, but for that we'd require super user access just to read the
    # file, which is just not a good idea.
    #
    # So instead we use the same mechanism that RPi OS uses to show the nag screen on the
    # command prompt, with the downside that it won't trigger if SSH is disabled for
    # whatever reason.
    return os.path.exists(_SSHWARN_PATH)


class PiSupportPlugin(
    octoprint.plugin.EnvironmentDetectionPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SettingsPlugin,
):
    # noinspection PyMissingConstructor
    def __init__(self):
        self._throttle_state = ThrottleState()
        self._throttle_check = None
        self._throttle_undervoltage = False
        self._throttle_overheat = False
        self._throttle_check_enabled = True
        self._throttle_check_functional = True

    def initialize(self):
        self._throttle_check_enabled = self._settings.get_boolean(
            ["vcgencmd_throttle_check_enabled"]
        )
        if not self._throttle_check_enabled:
            self._logger.warning(
                "Throttle check via vcgencmd disabled by user. Potential undervoltage or overheating issues will not be detected."
            )

    # Additional permissions hook

    def get_additional_permissions(self):
        return [
            {
                "key": "STATUS",
                "name": "Status",
                "description": gettext(
                    "Allows to check for the Pi's throttling status and environment info"
                ),
                "roles": ["check"],
                "default_groups": [USER_GROUP],
            }
        ]

    # Additional bundle files hook

    def get_additional_bundle_files(self, *args, **kwargs):
        if is_octopi():
            result = {
                "haproxy.log": "/var/log/haproxy.log",
            }

            if is_new_camerastack():
                # new camera-streamer based camera stack
                files = _gather_new_camerastack_files()
                result.update(**files)

            else:
                # old mjpg-streamer based camera stack
                result["webcamd.log"] = "/var/log/webcamd.log"

            return result
        else:
            return {}

    ##~~ Additional health checks hook

    def get_additional_health_checks(self):
        from .health_checks import all_checks

        def health_check_factory(clz):
            def factory(settings):
                return clz(self, settings)

            factory.key = clz.key
            return factory

        return [health_check_factory(clz) for clz in all_checks]

    # ~~ EnvironmentDetectionPlugin

    def get_additional_environment(self):
        result = {"model": get_proc_dt_model()}

        self._check_throttled_state()
        result["throttle_check_enabled"] = self._throttle_check_enabled
        result["throttle_check_functional"] = self._throttle_check_functional
        if self._throttle_check_enabled and self._throttle_check_functional:
            result["throttle_state"] = self._throttle_state.raw_value_hex

        if is_octopi():
            result["octopi_version"] = get_octopi_version()
            result["octopi_camera_stack"] = (
                "camera-streamer" if is_new_camerastack() else "webcamd"
            )

        if is_octopiuptodate():
            result["octopiuptodate_build"] = get_octopiuptodate_build()
            try:
                build = result["octopiuptodate_build"].split("-")[-1]

                result["octopiuptodate_build_short"] = (
                    build[0:4] + "." + build[4:6] + "." + build[6:8] + "." + build[8:]
                )
            except Exception:
                pass

        return result

    # ~~ SimpleApiPlugin

    def on_api_get(self, request):
        if not Permissions.PLUGIN_PI_SUPPORT_STATUS.can():
            return flask.abort(403)

        result = self.get_additional_environment()
        result.update(
            {
                "throttle_enabled": self._throttle_check_enabled,
                "throttle_functional": self._throttle_check_functional,
                "throttle_state": self._throttle_state.as_dict(),
                "model_unrecommended": is_model_any_of(
                    result.get("model"), *_UNRECOMMENDED_MODELS
                ),
                "default_password": has_default_password(),
            }
        )
        return flask.jsonify(**result)

    def is_api_protected(self):
        return True

    # ~~ AssetPlugin

    def get_assets(self):
        return {
            "js": ["js/pi_support.js"],
            "clientjs": ["clientjs/pi_support.js"],
            "css": ["css/pi_support.css"],
        }

    # ~~ TemplatePlugin

    def get_template_configs(self):
        configs = [
            {
                "type": "settings",
                "name": gettext("Pi Support"),
                "template": "pi_support_settings.jinja2",
                "custom_bindings": False,
            }
        ]

        if is_octopiuptodate():
            configs.append(
                {
                    "type": "about",
                    "name": "About OctoPi",
                    "template": "pi_support_about_octopiuptodate.jinja2",
                }
            )
        elif is_octopi():
            configs.append(
                {
                    "type": "about",
                    "name": "About OctoPi",
                    "template": "pi_support_about_octopi.jinja2",
                }
            )

        return configs

    def get_template_vars(self):
        return self.get_additional_environment()

    # ~~ StartupPlugin

    def on_startup(self, *args, **kwargs):
        if self._settings.get_boolean(["vcgencmd_throttle_check_enabled"]):
            self._check_throttled_state()
            self._throttle_check = RepeatedTimer(
                self._check_throttled_state_interval,
                self._check_throttled_state,
                condition=self._check_throttled_state_condition,
            )
            self._throttle_check.start()

    # ~~ SettingsPlugin

    def get_settings_defaults(self):
        return {
            "vcgencmd_throttle_check_enabled": True,
            "vcgencmd_throttle_check_command": _VCGENCMD_THROTTLE,
            "ignore_unrecommended_model": False,
            "ignore_undervoltage_on_printstart": False,
            "ignore_default_password": False,
        }

    def get_settings_restricted_paths(self):
        return {
            "admin": [
                ["vcgencmd_throttle_check_enabled"],
                ["vcgencmd_throttle_check_command"],
            ]
        }

    ##~~ Softwareupdate hook

    def get_update_information(self):
        return {
            "pi_support": {
                "displayName": "Pi Support Plugin",
                "displayVersion": self._plugin_version,
                # version check: github repository
                "type": "github_release",
                "user": "OctoPrint",
                "repo": "OctoPrint-PiSupport",
                "current": self._plugin_version,
                "stable_branch": {
                    "name": "Stable",
                    "branch": "main",
                    "commitish": ["devel", "main"],
                },
                "prerelease_branches": [
                    {
                        "name": "Prerelease",
                        "branch": "devel",
                        "commitish": ["devel", "main"],
                    }
                ],
                # update method: pip
                "pip": "https://github.com/OctoPrint/OctoPrint-PiSupport/archive/{target_version}.zip",
            }
        }

    # ~~ Helpers

    def _check_throttled_state_interval(self):
        if self._throttle_state.current_issue:
            return _CHECK_INTERVAL_THROTTLED
        else:
            return _CHECK_INTERVAL_OK

    def _check_throttled_state_condition(self):
        return self._throttle_check_enabled and self._throttle_check_functional

    def get_throttle_state(self, run_now=False):
        """Exposed as public helper."""
        if run_now:
            self._check_throttled_state()

        if not self._throttle_check_enabled or not self._throttle_check_functional:
            return False

        return self._throttle_state.as_dict()

    def _check_throttled_state(self):
        if not self._throttle_check_enabled:
            return

        command = self._settings.get(["vcgencmd_throttle_check_command"])

        self._logger.debug(f"Retrieving throttle state via {command!r}")
        try:
            state = get_vcgencmd_throttled_state(command)
        except ValueError as ex:
            error = str(ex)
            self._logger.warning(error)
            if "VCHI initialization failed" in error:
                self._logger.warning(
                    'Make sure the system user "{}" is in the "video" group.'.format(
                        getuser()
                    )
                )
            self._throttle_check_functional = False
            return

        if self._throttle_state == state:
            # no change
            return

        self._throttle_state = state

        if (not self._throttle_undervoltage and self._throttle_state.undervoltage) or (
            not self._throttle_overheat and self._throttle_state.overheat
        ):
            message = (
                "This Raspberry Pi is reporting problems that might lead to bad performance or errors caused "
                "by overheating or insufficient power."
            )

            if self._throttle_state.undervoltage:
                self._throttle_undervoltage = True
                message += (
                    "\n!!! UNDERVOLTAGE REPORTED !!! Make sure that the power supply and power cable are "
                    "capable of supplying enough voltage and current to your Pi."
                )

            if self._throttle_state.overheat:
                self._throttle_overheat = True
                message += (
                    "\n!!! FREQUENCY CAPPING DUE TO OVERHEATING REPORTED !!! Improve cooling on the Pi's "
                    "CPU and GPU."
                )

            self._logger.warning(message)

        self._plugin_manager.send_plugin_message(
            self._identifier,
            {"type": "throttle_state", "state": self._throttle_state.as_dict()},
        )

        # noinspection PyUnresolvedReferences
        self._event_bus.fire(
            octoprint.events.Events.PLUGIN_PI_SUPPORT_THROTTLE_STATE,
            self._throttle_state.as_dict(),
        )

        if hasattr(octoprint.events.Events, "PLUGIN_HEALTH_CHECK_UPDATE_HEALTHCHECK"):
            self._event_bus.fire(
                octoprint.events.Events.PLUGIN_HEALTH_CHECK_UPDATE_HEALTHCHECK
            )


def register_custom_events(*args, **kwargs):
    return [
        "throttle_state",
    ]


__plugin_name__ = "Pi Support Plugin"
__plugin_author__ = "Gina Häußge"
__plugin_description__ = "Provides additional information about your Pi in the UI."
__plugin_disabling_discouraged__ = gettext(
    "Without this plugin OctoPrint will no longer be able to "
    "provide additional information about your Pi, "
    "which will make it more tricky to help you if you need support."
)
__plugin_license__ = "AGPLv3"
__plugin_pythoncompat__ = ">=2.7,<4"


def __plugin_check__():
    try:
        proc_dt_model = get_proc_dt_model()
        if proc_dt_model is None:
            return False
    except Exception:
        return False

    return "raspberry pi" in proc_dt_model.lower()


def __plugin_load__():
    plugin = PiSupportPlugin()
    global __plugin_implementation__
    __plugin_implementation__ = plugin

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.events.register_custom_events": register_custom_events,
        "octoprint.access.permissions": __plugin_implementation__.get_additional_permissions,
        "octoprint.systeminfo.additional_bundle_files": __plugin_implementation__.get_additional_bundle_files,
        "octoprint.plugin.health_check.get_additional_checks": __plugin_implementation__.get_additional_health_checks,
    }

    global __plugin_helpers__
    __plugin_helpers__ = {"get_throttled": plugin.get_throttle_state}
