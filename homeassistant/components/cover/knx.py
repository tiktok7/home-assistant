"""
Support for KNX covers.

cover:
  - platform: knx
    updown_address: 9/0/0
    stop_address: 9/0/1
    setposition_address: 9/0/3
    getposition_address: 9/0/4

"""
import logging

import voluptuous as vol

from homeassistant.components.cover import (
    CoverDevice, PLATFORM_SCHEMA, ATTR_POSITION
)
from homeassistant.components.knx import (KNXConfig, KNXMultiAddressDevice)
from homeassistant.const import (CONF_NAME)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_UPDOWN = 'updown_address'
CONF_STOP = 'stop_address'
CONF_SETPOSITION_ADDRESS = 'setposition_address'
CONF_GETPOSITION_ADDRESS = 'getposition_address'

DEFAULT_NAME = 'KNX Cover'
DEPENDENCIES = ['knx']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_UPDOWN): cv.string,
    vol.Required(CONF_STOP): cv.string,
    vol.Optional(CONF_SETPOSITION_ADDRESS): cv.string,
    vol.Optional(CONF_GETPOSITION_ADDRESS): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Create and add an entity based on the configuration."""
    add_devices([KNXCover(hass, KNXConfig(config))])


class KNXCover(KNXMultiAddressDevice, CoverDevice):
    """Representation of a KNX cover. e.g. a rollershutter"""

    def __init__(self, hass, config):
        """Initialize the cover."""
        KNXMultiAddressDevice.__init__(
            self, hass, config,
            ['updown', 'stop'],  # required
            optional=['setposition', 'getposition']
        )

        self._hass = hass
        self._current_pos = None

    @property
    def should_poll(self):
        """Polling is needed for the KNX cover."""
        return True

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self.current_cover_position is not None:
            if self.current_cover_position > 0:
                return False
            else:
                return True

    @property
    def current_cover_position(self):
        """Return current position of cover.

        None is unknown, 0 is closed, 100 is fully open.
        """
        return self._current_pos

    @property
    def target_position(self):
        """Return the position we are trying to reach. 0 - 100"""
        return self._target_pos

    def set_percentage(self, name, percentage):
        value = (100 - percentage) * 255 // 100
        self.set_int_value(name, value)

    def get_percentage(self, name):
        value = self.get_int_value(name)
        percentage = (255 - value) * 100 // 255
        return percentage

    def set_int_value(self, name, value, num_bytes=1):
        # KNX packets are big endian
        b_value = value.to_bytes(num_bytes, byteorder='big')
        self.set_value(name, list(b_value))

    def get_int_value(self, name):
        # KNX packets are big endian
        sum = 0
        raw_value = self.value(name)
        if isinstance(raw_value, list) or isinstance(raw_value, bytes):
            for val in raw_value:
                sum *= 256
                sum += val

        return sum

    def set_cover_position(self, **kwargs):
        """Set new target position."""
        position = kwargs.get(ATTR_POSITION)
        if position is None:
            return

        self._target_pos = position
        self.set_percentage('setposition', position)
        _LOGGER.debug(
            "{}: Set target position to {:d}".format(
                self.name, position
            )
        )

    def update(self):
        """Update device state."""
        super().update()
        value = self.get_percentage('getposition')
        if value is not None:
            self._current_pos = value
        _LOGGER.debug("{}: position = {:d}".format(self.name, value))

    def open_cover(self, **kwargs):
        """Open the cover."""
        _LOGGER.debug("{}: open: updown = 0".format(self.name))
        self.set_int_value('updown', 0)

    def close_cover(self, **kwargs):
        """Close the cover."""
        _LOGGER.debug("{}: open: updown = 1".format(self.name))
        self.set_int_value('updown', 1)

    def stop_cover(self, **kwargs):
        """Stop the cover movement."""
        _LOGGER.debug("{}: stop: stop = 1".format(self.name))
        self.set_int_value('stop', 1)
