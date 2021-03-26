# Pi Support

The Pi Support plugin provides additional information about your Pi in the UI and also
alerts you about undervoltage or overheating issues observed on your Pi or if your Pi is
unsupported. If you are running OctoPi, the Pi Support plugin will also provide additional
information about that.

OctoPrint will only load this plugin when it detects that it is being run on a
Raspberry Pi.

This plugin was bundled right with OctoPrint's sources until version 1.6.0. It has been
extracted into a standalone project to allow for a different release cycle, but is still
considered a bundled plugin.

## Setup

The plugin is part of the core dependencies of OctoPrint 1.6.0+ and will be installed automatically alongside it.

In case you want to manually install it into an older version for whatever reason, install via the bundled
[Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/OctoPrint/OctoPrint-PiSupport/archive/main.zip

To install and/or rollback to a specific version `<version>`, either use this URL in the plugin manager:

    https://github.com/OctoPrint/OctoPrint-PiSupport/archive/<version>.zip

or run

    pip install OctoPrint-PiSupport==<version>

in your OctoPrint virtual environment, substituting `<version>` accordingly.

## Events

### plugin_pi_support_throttle_state

*(as `Events.PLUGIN_PI_SUPPORT_THROTTLE_STATE`)*

A change in throttle state was detected.

Payload:
  * `raw_value`: The raw throttle state value as received from `vcgencmd get_throttled`
  * `current_undervolate`: Whether there is currently an undervoltage condition
  * `past_undervoltage`: Whether there has been an undervoltage condition since last boot
  * `current_overheat`: Whether there is currently an overheat condition
  * `past_overheat`: Whether there has been an overheat condition since last boot
  * `current_issue`: Whether there is currently an undervoltage or overheat condition
  * `past_issue`: Whether there has been either an undervoltage or overheat condition since last boot

## Helpers

### get_throttled

Access to `get_throttle_state`, to retrieve the current throttle state. Returns a `dict`
with the same fields as the `PLUGIN_PI_SUPPORT_THROTTLE_STATE` event payload. By setting
the keyword argument `run_now` set to `True`, the throttle state will be refreshed before
returning.
