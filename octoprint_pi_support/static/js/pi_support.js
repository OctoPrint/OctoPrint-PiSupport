$(function () {
    function PiSupportViewModel(parameters) {
        var self = this;

        const UNDERVOLTAGE_TITLE = gettext("Undervoltage detected");
        const UNDERVOLTAGE_WARNING = gettext(
            "Your Raspberry Pi is reporting insufficient power. " +
                "Switch to an adequate power supply or risk bad " +
                "performance and failed prints."
        );
        const UNDERVOLTAGE_FAQ = "https://faq.octoprint.org/pi-issues";

        const ZERO_TITLE = gettext("Unsupported hardware detected");
        const ZERO_WARNING = gettext(
            "OctoPrint does not and never has supported the " +
                "RPi Zero or Zero W. Use at least a Raspberry Pi 3 or Zero 2, or " +
                "risk bad performance and failed prints."
        );
        const ZERO_DISABLE = gettext(
            "You can disable this message via Settings > " +
                "Pi Support > Disable warning about unsupported hardware"
        );
        const ZERO_FAQ = "https://faq.octoprint.org/recommended-hardware";

        const PASSWORD_TITLE = gettext("Default system password not changed");
        const PASSWORD_WARNING = gettext(
            'The default password for the system user "pi" has not ' +
                "been changed. This is a security risk - please login to " +
                "your Pi via SSH and change the password."
        );
        const PASSWORD_DISABLE = gettext(
            "You can disable this message via Settings > " +
                "Pi Support > Disable warning about default system password"
        );
        const PASSWORD_FAQ = "https://faq.octoprint.org/pi-default-password";

        const FAQ = gettext(
            'You can read more <a href="%(url)s" target="_blank">in the FAQ</a>.'
        );

        const generateHtml = (warning, faq, disable) => {
            const html =
                "<p>" +
                warning +
                "</p><p>" +
                _.sprintf(FAQ, {
                    url: faq
                }) +
                "</p>";

            if (disable) {
                return html + "<p><small>" + disable + "</small></p>";
            } else {
                return html;
            }
        };

        self.loginState = parameters[0];
        self.access = parameters[1];
        self.settings = parameters[2];

        self.model = ko.observable();

        self.currentUndervoltage = ko.observable(false);
        self.currentOverheat = ko.observable(false);
        self.pastUndervoltage = ko.observable(false);
        self.pastOverheat = ko.observable(false);
        self.currentIssue = ko.observable(false);
        self.pastIssue = ko.observable(false);

        self.notifications = {};

        self.requestData = function () {
            if (
                !self.loginState.hasPermission(
                    self.access.permissions.PLUGIN_PI_SUPPORT_STATUS
                )
            ) {
                return;
            }

            OctoPrint.plugins.pi_support.get().done(function (response) {
                // Raspberry Pi model
                self.model(response.model);

                // Unrecommended model
                if (
                    response.model_unrecommended &&
                    !self.settings.settings.plugins.pi_support.ignore_unrecommended_model()
                ) {
                    if (self.notifications.unrecommended === undefined) {
                        self.notifications.unrecommended = new PNotify({
                            title: ZERO_TITLE,
                            text: generateHtml(ZERO_WARNING, ZERO_FAQ, ZERO_DISABLE),
                            type: "error",
                            hide: false
                        });
                    }
                } else if (self.notifications.unrecommended !== undefined) {
                    self.notifications.unrecommended.remove();
                    self.notifications.unrecommended = undefined;
                }

                // Throttle functional
                if (!response.throttle_functional) {
                    var warning = gettext(
                        "OctoPrint cannot check for throttling situations " +
                            "reported by your Pi. <code>vcgencmd</code> doesn't work as expected. Make " +
                            "sure the system user OctoPrint is running under is a member of " +
                            'the "video" group.'
                    );

                    if (self.notifications.vcgencmd_broken === undefined) {
                        self.notifications.vcgencmd_broken = new PNotify({
                            title: gettext("Cannot check for throttling"),
                            text: "<p>" + warning + "</p>",
                            hide: false
                        });
                    }
                } else if (self.notifications.vcgencmd_broken !== undefined) {
                    self.notifications.vcgencmd_broken.remove();
                    self.notifications.vcgencmd_broken = undefined;
                }

                // Throttle state
                self.fromThrottleState(response.throttle_state);
                if (self.currentUndervoltage() || self.pastUndervoltage()) {
                    if (self.notifications.throttled === undefined) {
                        self.notifications.throttled = new PNotify({
                            title: UNDERVOLTAGE_TITLE,
                            text: generateHtml(UNDERVOLTAGE_WARNING, UNDERVOLTAGE_FAQ),
                            type: "error",
                            hide: false
                        });
                    }
                } else if (self.notifications.throttled !== undefined) {
                    self.notifications.throttled.remove();
                    self.notifications.throttled = undefined;
                }

                // SSH warn
                if (
                    response.default_password &&
                    !self.settings.settings.plugins.pi_support.ignore_default_password()
                ) {
                    if (self.notifications.default_password === undefined) {
                        self.notifications.default_password = new PNotify({
                            title: PASSWORD_TITLE,
                            text: generateHtml(
                                PASSWORD_WARNING,
                                PASSWORD_FAQ,
                                PASSWORD_DISABLE
                            ),
                            hide: false
                        });
                    }
                } else if (self.notifications.default_password !== undefined) {
                    self.notifications.default_password.remove();
                    self.notifications.default_password = undefined;
                }

                // OctoPi version
                $("#pi_support_footer").remove();
                if (!response.octopi_version) return;

                if (response.octopiuptodate_build_short) {
                    let cam_suffix =
                        response.octopi_camera_stack == "camera-streamer" ? "cam" : "";
                    var octoPiVersion = $(
                        "<li id='pi_support_footer'><small>" +
                            gettext("OctoPi") +
                            "* " +
                            "<span class='octopi_version'>" +
                            response.octopi_version +
                            cam_suffix +
                            " (build " +
                            response.octopiuptodate_build_short +
                            ")" +
                            "</span></small></li>"
                    );
                    $("#footer_version").append(octoPiVersion);
                } else {
                    var octoPiVersion = $(
                        "<li id='pi_support_footer'><small>" +
                            gettext("OctoPi") +
                            " " +
                            "<span class='octopi_version'>" +
                            response.octopi_version +
                            "</span></small></li>"
                    );
                    $("#footer_version").append(octoPiVersion);
                }
            });
        };

        self.fromThrottleState = function (state) {
            self.currentUndervoltage(state.current_undervoltage);
            self.pastUndervoltage(state.past_undervoltage);
            self.currentOverheat(state.current_overheat);
            self.pastOverheat(state.past_overheat);
            self.currentIssue(state.current_issue);
            self.pastIssue(state.past_issue);
        };

        self.popoverContent = ko.pureComputed(function () {
            var content = "";
            var undervoltageParagraph =
                '<p><strong><i class="fa fa-bolt"></i><i class="fa fa-exclamation"></i> Undervoltage:</strong> ' +
                gettext(
                    "Make sure your power supply and cabling are providing enough power to the Pi."
                ) +
                "</p>";
            var overheatParagraph =
                '<p><strong><i class="fa fa-thermometer-full"></i><i class="fa fa-exclamation"></i> Overheating:</strong> ' +
                gettext(
                    "Frequency capping due to overheating. Improve cooling of the CPU and GPU."
                ) +
                "</p>";

            if (self.currentIssue()) {
                content += "<p><strong>" + gettext("Current issues:") + "</strong></p>";
                content +=
                    "<p><small>" +
                    gettext(
                        "The following issues are being observed <em>right now</em>:"
                    ) +
                    "</small></p>";
                if (self.currentUndervoltage()) {
                    content += undervoltageParagraph;
                }
                if (self.currentOverheat()) {
                    content += overheatParagraph;
                }
            }

            if (self.currentIssue() && self.pastIssue()) {
                content += "<hr>";
            }

            if (self.pastIssue()) {
                content +=
                    "<p><strong>" + gettext("Issues since boot:") + "</strong></p>";
                content +=
                    "<p><small>" +
                    gettext(
                        "The following issues have been observed since the Pi was booted:"
                    ) +
                    "</small></p>";
                if (self.pastUndervoltage() && !self.currentUndervoltage()) {
                    content += undervoltageParagraph;
                }
                if (self.pastOverheat() && !self.currentOverheat()) {
                    content += overheatParagraph;
                }
            }

            content +=
                "<hr><p><small>" +
                gettext("Click the navbar icon for more information.") +
                "</small></p>";

            return content;
        });

        self.onStartup =
            self.onServerReconnect =
            self.onUserLoggedIn =
            self.onUserLoggedOut =
                function () {
                    self.requestData();
                };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "pi_support") return;
            if (!data.hasOwnProperty("state") || !data.hasOwnProperty("type")) return;
            if (data.type !== "throttle_state") return;
            if (
                !self.loginState.hasPermission(
                    self.access.permissions.PLUGIN_PI_SUPPORT_STATUS
                )
            )
                return;

            self.fromThrottleState(data.state);
        };

        self.onBeforePrintStart = function (callback) {
            if (
                !self.settings.settings.plugins.pi_support.ignore_undervoltage_on_printstart() &&
                (self.currentUndervoltage() || self.pastUndervoltage())
            ) {
                showConfirmationDialog({
                    title: gettext("Undervoltage detected, print anyway?"),
                    message:
                        gettext(
                            "Your Pi is reporting undervoltage. It is not recommended to start a print job until an adequate power supply has been installed."
                        ) +
                        " <a href='https://faq.octoprint.org/pi-issues' target='_blank'>" +
                        gettext("See also the FAQ") +
                        "</a>.",
                    question: gettext("Start the print job anyway?"),
                    cancel: gettext("No, don't print"),
                    proceed: [
                        gettext("Yes, print"),
                        gettext("Yes, print & don't warn again")
                    ],
                    onproceed: function (idx) {
                        if (idx === 1) {
                            self.settings.settings.plugins.pi_support.ignore_undervoltage_on_printstart(
                                true
                            );
                            self.settings.saveData();
                        }
                        callback();
                    },
                    nofade: true
                });
                return false;
            }
        };

        self.getAdditionalHealthCheckHandlers = function () {
            return {
                pi_undervoltage: (result, context) => {
                    return {
                        title: UNDERVOLTAGE_TITLE,
                        html: generateHtml(UNDERVOLTAGE_WARNING, UNDERVOLTAGE_FAQ),
                        result: result
                    };
                },
                pi_unsupported: (result, context) => {
                    return {
                        title: ZERO_TITLE,
                        html: generateHtml(ZERO_WARNING, ZERO_FAQ),
                        result: result
                    };
                },
                pi_default_password: (result, context) => {
                    return {
                        title: PASSWORD_TITLE,
                        html: generateHtml(PASSWORD_WARNING, PASSWORD_FAQ),
                        result: result
                    };
                }
            };
        };
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: PiSupportViewModel,
        elements: ["#navbar_plugin_pi_support"],
        dependencies: ["loginStateViewModel", "accessViewModel", "settingsViewModel"]
    });
});
