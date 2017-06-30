"""
Support KNX Lighting actuators.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/Light.knx/
"""
import logging
import voluptuous as vol

from homeassistant.components.knx import (KNXConfig, KNXMultiAddressDevice)
from homeassistant.components.light import (
    Light, PLATFORM_SCHEMA, ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS
)
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_ADDRESS = 'address'
CONF_STATE_ADDRESS = 'state_address'
CONF_BRIGHTNESS_ADDRESS = 'brightness_address'
CONF_DIMMER_ADDRESS = 'dimmer_address'

CONF_MSG_BRIGHTNESS = \
    "Missing either dimmer address or brightness address."

DEFAULT_NAME = 'KNX Light'
DEPENDENCIES = ['knx']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ADDRESS): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_STATE_ADDRESS): cv.string,
    vol.Inclusive(
        CONF_BRIGHTNESS_ADDRESS, 'brightness', CONF_MSG_BRIGHTNESS
    ): cv.string,
    vol.Inclusive(
        CONF_DIMMER_ADDRESS, 'brightness', CONF_MSG_BRIGHTNESS
    ): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the KNX light platform."""
    add_devices([KNXLight(hass, KNXConfig(config))])


class KNXLight(KNXMultiAddressDevice, Light):
    """Representation of a KNX Light device."""

    def __init__(self, hass, config):
        """Initialize the cover."""
        KNXMultiAddressDevice.__init__(
            self, hass, config,
            [],  # required
            optional=[
                # state_address is automatically processed by
                # KNXMultiAddressDevice
                'brightness', 'dimmer'
            ]
        )
        self._hass = hass
        self._brightness = None
        self._state = None
        self._supported_features = 0
        self._supported_features |= (
            config.config.get(CONF_DIMMER_ADDRESS) is not None and
            SUPPORT_BRIGHTNESS)
        _LOGGER.debug("KNXLight config: {}".format(config.config))

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._supported_features

    @property
    def brightness(self):
        """Return the brightness level of the light."""
        return self._brightness

    @property
    def is_on(self):
        """Return true if the light is on."""
        return self._state

    @property
    def should_poll(self):
        """Polling is needed for the KNX dimmer status."""
        return True

    def update(self):
        """Update device state."""
        super().update()

        if self.has_attribute('state'):
            value = self.get_int_value('state')
            if value is not None:
                self._state = value
                _LOGGER.debug("%s: read state = %d", self.name, value)

        if self.supported_features & SUPPORT_BRIGHTNESS:
            value = self.get_int_value('brightness')
            if value is not None:
                self._brightness = value
                _LOGGER.debug("%s: read brightness = %d", self.name, value)

    def turn_on(self, **kwargs):
        """Turn the light on.

        This sends a value 1 to the group address of the device.  It also
        writes the brightness if either the brightness or brightness_pct
        keyword is used.

        """
        _LOGGER.debug(
            "%s: turn on with parameters: %s",
            self.name, str(kwargs)
        )
        self.set_int_value('base', 1)
        self._state = 1

        # dimming support
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None:
            _LOGGER.debug("%s: set brightness = %d", self.name, brightness)
            res = self.set_int_value('dimmer', brightness)
            if res is not None:
                self._brightness = brightness

    def turn_off(self, **kwargs):
        """Turn the switch off.

        This sends a value 0 to the group address of the device
        """
        _LOGGER.debug("%s: turn off", self.name)
        self.set_int_value('base', 0)
        self._state = 0
