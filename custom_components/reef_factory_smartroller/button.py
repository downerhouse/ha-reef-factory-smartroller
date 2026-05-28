"""Button platform for Reef Factory Smart Roller."""

from __future__ import annotations

from homeassistant.components.button import (
    ButtonEntity,
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

from .const import (
    DOMAIN,
    SIGNAL_CONNECTION_STATE,
    SIGNAL_DATA_UPDATED,
)
from .coordinator import ReeffactoryCoordinator


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
            SmartRollerManualAdvanceButton(
                coordinator
            ),
            SmartRollerRestartButton(
                coordinator
            ),
            SmartRollerReplaceRollButton(
                coordinator
            ),
        ]
    )


class SmartRollerManualAdvanceButton(
    ButtonEntity
):

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:

        self._coordinator = coordinator

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_manual_advance"
        )

        self._attr_name = (
            "Execute Manual Advance"
        )

        self._attr_icon = (
            "mdi:arrow-down-bold-box-outline"
        )

        self._attr_device_info = (
            coordinator.device_info
        )

    @property
    def available(self) -> bool:

        return self._coordinator.available

    async def async_added_to_hass(self):

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_CONNECTION_STATE,
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self, available):

        self.async_write_ha_state()

    async def async_press(self) -> None:

        await self._coordinator.async_manual_advance(
            self._coordinator.manual_advance_mm
        )


class SmartRollerRestartButton(
    ButtonEntity
):

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:

        self._coordinator = coordinator

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_restart"
        )

        self._attr_name = (
            "Restart Roller"
        )

        self._attr_icon = (
            "mdi:restart"
        )

        self._attr_device_info = (
            coordinator.device_info
        )

    @property
    def available(self) -> bool:

        return (
            self._coordinator.available
            and self._coordinator.data.get(
                "roller_status"
            ) == "Jammed"
        )

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

    async def async_press(self) -> None:

        await self._coordinator.async_unblock()
        
class SmartRollerReplaceRollButton(
    ButtonEntity
):

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:

        self._coordinator = coordinator

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_replace_roll"
        )

        self._attr_name = (
            "Apply Roll Replacement"
        )

        self._attr_icon = (
            "mdi:roller"
        )

        self._attr_device_info = (
            coordinator.device_info
        )

    @property
    def available(self) -> bool:

        return self._coordinator.available

    async def async_added_to_hass(self):

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_CONNECTION_STATE,
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self, available):

        self.async_write_ha_state()

    async def async_press(self) -> None:

        await self._coordinator.async_replace_roll()