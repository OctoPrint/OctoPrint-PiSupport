import unittest
from unittest import mock

import ddt
from octoprint.util.platform import CLOSE_FDS

OCTOPI_VERSION = "0.14.0"

OCTOPI_UPTODATE_BUILD = "0.18.0-1.7.2-20220119085355"

DT_MODEL = "Raspberry Pi Model F Rev 1.1"

VCGENCMD = "/usr/bin/vcgencmd get_throttled"

OPEN_SIGNATURE = "builtins.open"


class PiSupportTestCase(unittest.TestCase):
    def test_get_octopi_version(self):
        from octoprint_pi_support import get_octopi_version

        # import _fixups

        with mock.patch(OPEN_SIGNATURE, mock.mock_open(), create=True) as m:
            m.return_value.readline.return_value = OCTOPI_VERSION
            version = get_octopi_version()

        m.assert_called_once_with("/etc/octopi_version", encoding="utf-8")
        self.assertEqual(version, OCTOPI_VERSION)

    def test_get_octopiuptodate_build(self):
        from octoprint_pi_support import get_octopiuptodate_build

        with mock.patch(OPEN_SIGNATURE, mock.mock_open(), create=True) as m:
            m.return_value.readline.return_value = OCTOPI_UPTODATE_BUILD
            build = get_octopiuptodate_build()

        m.assert_called_once_with("/etc/octopiuptodate_build", encoding="utf-8")
        self.assertEqual(build, OCTOPI_UPTODATE_BUILD)

    def test_get_proc_dt_model(self):
        from octoprint_pi_support import get_proc_dt_model

        with mock.patch(OPEN_SIGNATURE, mock.mock_open(), create=True) as m:
            m.return_value.readline.return_value = DT_MODEL
            model = get_proc_dt_model()

        m.assert_called_once_with("/proc/device-tree/model", encoding="utf-8")
        self.assertEqual(model, DT_MODEL)

    def test_get_vcgencmd_throttle_state(self):
        from octoprint_pi_support import get_vcgencmd_throttled_state

        with mock.patch("sarge.get_both", mock.MagicMock()) as m:
            m.return_value = ("throttled=0x70005", "")
            state = get_vcgencmd_throttled_state(VCGENCMD)

        m.assert_called_once_with(VCGENCMD, close_fds=CLOSE_FDS)
        self.assertTrue(state.current_undervoltage)
        self.assertFalse(state.current_overheat)
        self.assertTrue(state.current_issue)
        self.assertTrue(state.past_undervoltage)
        self.assertTrue(state.past_overheat)
        self.assertTrue(state.past_issue)

    def test_get_vcgencmd_throttle_state_unparseable1(self):
        from octoprint_pi_support import get_vcgencmd_throttled_state

        with mock.patch("sarge.get_both", mock.MagicMock()) as m:
            m.return_value = ("", "invalid")

            try:
                get_vcgencmd_throttled_state(VCGENCMD)
            except ValueError:
                # expected
                pass
            else:
                self.fail("Expected ValueError")

    def test_get_vcgencmd_throttle_state_unparseable2(self):
        from octoprint_pi_support import get_vcgencmd_throttled_state

        with mock.patch("sarge.get_both", mock.MagicMock()) as m:
            m.return_value = ("throttled=0xinvalid", "")

            try:
                get_vcgencmd_throttled_state(VCGENCMD)
            except ValueError:
                # expected
                pass
            else:
                self.fail("Expected ValueError")


@ddt.ddt
class ThrottleStateTestCase(unittest.TestCase):
    @ddt.data(
        (
            0x00000,
            {
                "_undervoltage": False,
                "_freq_capped": False,
                "_throttled": False,
                "_past_undervoltage": False,
                "_past_freq_capped": False,
                "_past_throttled": False,
                "current_undervoltage": False,
                "past_undervoltage": False,
                "current_overheat": False,
                "past_overheat": False,
                "current_issue": False,
                "past_issue": False,
            },
        ),
        (
            0x50005,
            {
                "_undervoltage": True,
                "_freq_capped": False,
                "_throttled": True,
                "_past_undervoltage": True,
                "_past_freq_capped": False,
                "_past_throttled": True,
                "current_undervoltage": True,
                "past_undervoltage": True,
                "current_overheat": False,
                "past_overheat": False,
                "current_issue": True,
                "past_issue": True,
            },
        ),
        (
            0x50000,
            {
                "_undervoltage": False,
                "_freq_capped": False,
                "_throttled": False,
                "_past_undervoltage": True,
                "_past_freq_capped": False,
                "_past_throttled": True,
                "current_undervoltage": False,
                "past_undervoltage": True,
                "current_overheat": False,
                "past_overheat": False,
                "current_issue": False,
                "past_issue": True,
            },
        ),
        (
            0x00006,
            {
                "_undervoltage": False,
                "_freq_capped": True,
                "_throttled": True,
                "_past_undervoltage": False,
                "_past_freq_capped": False,
                "_past_throttled": False,
                "current_undervoltage": False,
                "past_undervoltage": False,
                "current_overheat": True,
                "past_overheat": False,
                "current_issue": True,
                "past_issue": False,
            },
        ),
    )
    @ddt.unpack
    def test_conversion(self, input, expected_flags):
        from octoprint_pi_support import ThrottleState

        output = ThrottleState.from_value(input)

        for key, value in expected_flags.items():
            self.assertEqual(getattr(output, key), value)

    def test_as_dict(self):
        from octoprint_pi_support import ThrottleState

        state = ThrottleState(
            undervoltage=True,
            throttled=True,
            past_undervoltage=True,
            past_freq_capped=True,
            past_throttled=True,
        )

        self.assertDictEqual(
            state.as_dict(),
            {
                "current_undervoltage": True,
                "past_undervoltage": True,
                "current_overheat": False,
                "past_overheat": True,
                "current_issue": True,
                "past_issue": True,
                "raw_value": -1,
            },
        )
