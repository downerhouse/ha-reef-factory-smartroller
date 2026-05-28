from __future__ import annotations

from homeassistant.components.select import (
    SelectEntity,
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
    async_dispatcher_send,
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


SHIFT_OPTIONS = {
    "3 cm": 30,
    "4 cm": 40,
    "5 cm": 50,
    "6 cm": 60,
    "8 cm": 80,
    "10 cm": 100,
    "15 cm": 150,
}

DELAY_OPTIONS = {
    "0 seconds": 0,
    "30 seconds": 30,
    "1 min": 60,
    "5 min": 300,
    "15 min": 900,
    "30 min": 1800,
}

MANUAL_ADVANCE_OPTIONS = {
    "3 cm": 30,
    "4 cm": 40,
    "5 cm": 50,
    "6 cm": 60,
    "8 cm": 80,
    "10 cm": 100,
    "15 cm": 150,
}

ROLL_REPLACEMENT_OPTIONS = {
    "New Roll": "new",
    "Used Roll": "used",
}


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
            SmartRollerShiftSelect(
                coordinator
            ),
            SmartRollerDelaySelect(
                coordinator
            ),
            SmartRollerManualAdvanceSelect(
                coordinator
            ),
            SmartRollerReplacementModeSelect(
                coordinator
            ),
        ]
    )


class SmartRollerBaseSelect(
    SelectEntity
):

    _attr_has_entity_name = True

    def __init__(self, coordinator):

        self._coordinator = coordinator

        self._attr_device_info = (
            coordinator.device_info
        )

    @property
    def available(self):

        return self._coordinator.available

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


class SmartRollerShiftSelect(
    SmartRollerBaseSelect
):

    _attr_name = "Shift Length"

    def __init__(self, coordinator):

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_shift_select"
        )

        self._attr_options = list(
            SHIFT_OPTIONS.keys()
        )

    @property
    def current_option(self):

        current = self._coordinator.data.get(
            "shift_mm"
        )

        for label, value in (
            SHIFT_OPTIONS.items()
        ):
            if value == current:
                return label

        return None

    async def async_select_option(
        self,
        option: str,
    ) -> None:

        await self._coordinator.async_set_settings(
            SHIFT_OPTIONS[option],
            self._coordinator.data.get(
                "delay_seconds",
                60,
            ),
            self._coordinator.data.get(
                "reminder",
                7,
            ),
        )


class SmartRollerDelaySelect(
    SmartRollerBaseSelect
):

    _attr_name = "Start Delay"

    def __init__(self, coordinator):

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_delay_select"
        )

        self._attr_options = list(
            DELAY_OPTIONS.keys()
        )

    @property
    def current_option(self):

        current = self._coordinator.data.get(
            "delay_seconds"
        )

        for label, value in (
            DELAY_OPTIONS.items()
        ):
            if value == current:
                return label

        return None

    async def async_select_option(
        self,
        option: str,
    ) -> None:

        await self._coordinator.async_set_settings(
            self._coordinator.data.get(
                "shift_mm",
                30,
            ),
            DELAY_OPTIONS[option],
            self._coordinator.data.get(
                "reminder",
                7,
            ),
        )


class SmartRollerManualAdvanceSelect(
    SmartRollerBaseSelect
):

    _attr_name = "Manual Advance"

    def __init__(self, coordinator):

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_manual_advance"
        )

        self._attr_options = list(
            MANUAL_ADVANCE_OPTIONS.keys()
        )

    @property
    def current_option(self):

        current = (
            self._coordinator.manual_advance_mm
        )

        for label, value in (
            MANUAL_ADVANCE_OPTIONS.items()
        ):
            if value == current:
                return label

        return "3 cm"

    async def async_select_option(
        self,
        option: str,
    ) -> None:

        self._coordinator.manual_advance_mm = (
            MANUAL_ADVANCE_OPTIONS[option]
        )

        self.async_write_ha_state()


class SmartRollerReplacementModeSelect(
    SmartRollerBaseSelect
):

    _attr_name = "Roll Replacement Mode"

    def __init__(self, coordinator):

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_replacement_mode"
        )

        self._attr_options = list(
            ROLL_REPLACEMENT_OPTIONS.keys()
        )

    @property
    def current_option(self):

        current = (
            self._coordinator.roll_replacement_mode
        )

        for label, value in (
            ROLL_REPLACEMENT_OPTIONS.items()
        ):
            if value == current:
                return label

        return "New Roll"

    async def async_select_option(
        self,
        option: str,
    ) -> None:

        self._coordinator.roll_replacement_mode = (
            ROLL_REPLACEMENT_OPTIONS[option]
        )

        async_dispatcher_send(
            self.hass,
            SIGNAL_DATA_UPDATED,
        )

        self.async_write_ha_state()