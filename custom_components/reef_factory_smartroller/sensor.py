"""Sensor platform for Reef Factory Smart Roller."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
)
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import DOMAIN, SIGNAL_DATA_UPDATED
from .coordinator import ReeffactoryCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Roller entities."""

    coordinator: ReeffactoryCoordinator = hass.data[
        DOMAIN
    ][entry.entry_id]

    async_add_entities(
        [
            SmartRollerRemainingSensor(
                coordinator
            ),
            SmartRollerTodayUsageSensor(
                coordinator
            ),
            SmartRollerDailyAverageSensor(
                coordinator
            ),
            SmartRollerAutoEnabledBinarySensor(
                coordinator
            ),
            SmartRollerStatusSensor(
                coordinator
            ),
        ]
    )


class SmartRollerBaseEntity:
    """Base entity."""

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:

        self._coordinator = coordinator

        self._attr_device_info = (
            coordinator.device_info
        )

    @property
    def available(self) -> bool:
        """Return True if device is connected."""

        return self._coordinator.available

    async def async_added_to_hass(
        self,
    ) -> None:
        """Subscribe to updates."""

        await super().async_added_to_hass()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_DATA_UPDATED,
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        """Handle updates."""

        self.async_write_ha_state()


class SmartRollerRemainingSensor(
    SmartRollerBaseEntity,
    SensorEntity,
):
    """Remaining fleece sensor."""

    _attr_has_entity_name = True
    _attr_name = "Remaining Fleece"
    _attr_native_unit_of_measurement = "m"
    _attr_icon = "mdi:roller-shade"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_remaining"
        )

    @property
    def native_value(self):
        """Return remaining fleece."""

        data = self._coordinator.data

        if not data:
            return None

        return round(
            data["remaining_mm"] / 1000,
            2,
        )


class SmartRollerTodayUsageSensor(
    SmartRollerBaseEntity,
    SensorEntity,
):
    """Today's fleece usage."""

    _attr_has_entity_name = True
    _attr_name = "Today Usage"
    _attr_native_unit_of_measurement = "m"
    _attr_icon = "mdi:chart-line"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_today_usage"
        )

    @property
    def native_value(self):
        """Return today's usage."""

        data = self._coordinator.data

        if not data:
            return None

        return round(
            data["today_mm"] / 1000,
            2,
        )


class SmartRollerDailyAverageSensor(
    SmartRollerBaseEntity,
    SensorEntity,
):
    """Daily average fleece usage."""

    _attr_has_entity_name = True
    _attr_name = "Daily Average"
    _attr_native_unit_of_measurement = "m/day"
    _attr_icon = "mdi:chart-bell-curve"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_daily_average"
        )

    @property
    def native_value(self):
        """Return daily average."""

        data = self._coordinator.data

        if not data:
            return None

        return round(
            data["daily_average_mm"] / 1000,
            2,
        )


class SmartRollerAutoEnabledBinarySensor(
    SmartRollerBaseEntity,
    BinarySensorEntity,
):
    """Automatic mode sensor."""

    _attr_has_entity_name = True
    _attr_name = "Automatic Mode"
    _attr_icon = "mdi:autorenew"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_automatic"
        )

    @property
    def is_on(self):
        """Return automatic mode state."""

        data = self._coordinator.data

        if not data:
            return None

        return data["auto_enabled"]


class SmartRollerStatusSensor(
    SmartRollerBaseEntity,
    SensorEntity,
):
    """Current roller status."""

    _attr_has_entity_name = True
    _attr_name = "Current Roller Status"
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_roller_status"
        )

    @property
    def native_value(self):

        return self._coordinator.data.get(
            "roller_status",
            "Unknown",
        )