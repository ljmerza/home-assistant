"""Travel Time component."""

from homeassistant.const import (
    CONF_NAME, CONF_UNIT_SYSTEM_METRIC,
    CONF_UNIT_SYSTEM_IMPERIAL, CONF_UNIT_OF_MEASUREMENT)
from homeassistant.helpers.entity import Entity, generate_entity_id
from homeassistant.helpers.location import has_location
from homeassistant.components.sensor import PLATFORM_SCHEMA

CONF_DESTINATION = 'destination'
CONF_ORIGIN = 'origin'

ATTR_DURATION = 'duration'
ATTR_DISTANCE = 'distance'

ICON = 'mdi:car'

_LOGGER = logging.getLogger(__name__)

domain = 'travel_time'
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)
UNITS = [CONF_UNIT_SYSTEM_METRIC, CONF_UNIT_SYSTEM_IMPERIAL]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DESTINATION): cv.string,
    vol.Optional(CONF_NAME, default='Travel Time'): cv.string
    vol.Required(CONF_ORIGIN): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT): vol.In(UNITS)
})

def get_location_from_attributes(entity):
    """Get the lat/long string from an entities attributes."""
    attr = entity.attributes
    return "%s,%s" % (attr.get(ATTR_LATITUDE), attr.get(ATTR_LONGITUDE))


class TravelTime(Entity):
    """A travel time component."""

    def __init__(self, hass, data):
        self._hass = hass

        self._destination = data.get(CONF_ORIGIN)
        self._name = data.get(CONF_NAME)
        self._origin = data.get(CONF_DESTINATION)

        units = config.get(CONF_UNIT_OF_MEASUREMENT)
        if units is None:
            units = hass.config.units.name

        self._origin_coordinates = None
        self._destination_coordinates = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._state is None:
            return None

        if ATTR_DURATION in self._state:
            return round(self._state[ATTR_DURATION])
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'min'

    def friendly_name(self):
        """Return the friendly name."""
        return self.entity_conf.get(CONF_NAME)

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            "origin": self._origin,
            "destination": self._destination,
            "origin_coordinates": self._origin_coordinates,
            "destination_coordinates": self._destination_coordinates,
        }

    def _get_location_from_entity(self, entity):
        """Get the location from the entity state or attributes."""

        # Check if the entity has location attributes
        if has_location(entity):
            return self._get_location_from_attributes(entity)

        # Check if device is in a zone
        zone_entity = self._hass.states.get("zone.%s" % entity.state)
        if has_location(zone_entity):
            _LOGGER.debug("getting zone location for %s",
                          zone_entity.entity_id)

            return get_location_from_attributes(zone_entity)

        # If zone was not found then use the state as the location
        return entity.state

    def _resolve_zone(self, friendly_name):
        entities = self._hass.states.all()
        for entity in entities:
            if entity.domain == 'zone' and entity.name == friendly_name:
                return get_location_from_attributes(entity)

        return friendly_name

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update():
        """Fetch new state data for the sensor."""
        # try to get origin coordinates from entity
        origin_entity = self._hass.states.get(self._origin)
        if origin_entity is not None:
            entity = self._get_location_from_entity(
                origin_entity)
            self._origin_coordinates = self._resolve_zone(entity)

        # try to get destination coordinates from entity
        destination_entity = self._hass.states.get(self._destination)
        if destination_entity is not None:
            entity = self._get_location_from_entity(
                destination_entity)
            self._destination_coordinates = self._resolve_zone(entity)

    