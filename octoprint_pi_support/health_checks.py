from . import (
    _UNRECOMMENDED_MODELS,
    get_proc_dt_model,
    has_default_password,
    is_model_any_of,
)

try:
    import octoprint.plugins.health_check.checks as checks
except ImportError:
    try:
        # in case we extract it into a standalone plugin in the future...
        import octoprint_health_check.checks as checks
    except ImportError:
        # apparently the plugin is disabled
        checks = None

if checks is not None:

    class PiSupportHealthCheck(checks.HealthCheck):
        def __init__(self, plugin, settings: dict):
            super().__init__(settings)
            self._plugin = plugin

    class PiUndervoltageHealthCheck(PiSupportHealthCheck):
        key = "pi_undervoltage"

        def perform_check(self, force=False):
            state = self._plugin.get_throttle_state()

            if state["current_undervoltage"]:
                return checks.CheckResult(result=checks.Result.ISSUE, context=state)
            elif state["past_undervoltage"]:
                return checks.CheckResult(result=checks.Result.WARNING, context=state)

    class PiUnsupportedHealthCheck(PiSupportHealthCheck):
        key = "pi_unsupported"

        def perform_check(self, force=False):
            model = get_proc_dt_model()
            if is_model_any_of(model, *_UNRECOMMENDED_MODELS):
                return checks.CheckResult(result=checks.Result.WARNING)

    class PiDefaultPasswordHealthCheck(PiSupportHealthCheck):
        key = "pi_default_password"

        def perform_check(self, force=False):
            if has_default_password():
                return checks.CheckResult(result=checks.Result.WARNING)

    all_checks = [
        PiUndervoltageHealthCheck,
        PiUnsupportedHealthCheck,
        PiDefaultPasswordHealthCheck,
    ]

else:
    all_checks = []
