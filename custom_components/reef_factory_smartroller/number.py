from __future__ import annotations

from homeassistant.components.number import (
    NumberEntity,
)

from homeassistant.config_entries import (
    ConfigEntry,
)

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

from .const import (
    DOMAIN,
    SIGNAL_DATA_UPDATED,
)

from .coordinator import (
    ReeffactoryCoordinator,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:

    coordinator: ReeffactoryCoordinator = hass.data[
        DOMAIN
    ][entry.entry_id]

    async_add_entities(
        [
            SmartRollerUsedRollDiameter(
                coordinator
            ),
        ]
    )


class SmartRollerUsedRollDiameter(
    NumberEntity
):

    _attr_has_entity_name = True

    _attr_name = (
        "Used Roll Diameter"
    )

    _attr_native_min_value = 45

    _attr_native_max_value = 140

    _attr_native_step = 1

    _attr_native_unit_of_measurement = "mm"

    _attr_icon = (
        "mdi:tape-measure"
    )

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:

        self._coordinator = coordinator

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_used_roll_diameter"
        )

        self._attr_device_info = (
            coordinator.device_info
        )

    @property
    def available(self):

        return (
            self._coordinator.available
            and self._coordinator.roll_replacement_mode
            == "used"
        )

    @property
    def native_value(self):

        return (
            self._coordinator.used_roll_diameter
        )

    async def async_set_native_value(
        self,
        value: float,
    ) -> None:

        self._coordinator.used_roll_diameter = (
            int(value)
        )

        self.async_write_ha_state()

    async def async_added_to_hass(self):

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_DATA_UPDATED,
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self):

        self.async_write_ha_state()