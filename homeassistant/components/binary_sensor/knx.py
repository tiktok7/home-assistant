"""
Contains functionality to use a KNX group address as a binary.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.knx/

binary_sensor:
  - platform: knx
    name: mybin
    address: 3/0/1

"""
import voluptuous as vol

from homeassistant.components.binary_sensor import (BinarySensorDevice,
                                                    PLATFORM_SCHEMA)
from homeassistant.components.knx import (KNXConfig, KNXGroupAddress)
from homeassistant.const import CONF_NAME, CONF_ADDRESS
import homeassistant.helpers.config_validation as cv

DEFAULT_NAME = 'KNX Binary Sensor'

DEPENDENCIES = ['knx']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ADDRESS): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the KNX binary sensor platform."""
    add_devices([KNXBinarySensor(hass, KNXConfig(config))])


class KNXBinarySensor(KNXGroupAddress, BinarySensorDevice):
    """Representation of a KNX binary sensor device."""

    def __init__(self, hass, config):
        """Initialize a KNX Binary Sensor."""
        self._value = None

        KNXGroupAddress.__init__(self, hass, config)

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return KNXGroupAddress.is_on
