"""WebSocket connection manager for Reef Factory Roller Mat."""

from __future__ import annotations

import asyncio
import logging
import time

import aiohttp

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    DOMAIN,
    PING_INTERVAL,
    PONG_TIMEOUT,
    SIGNAL_CONNECTION_STATE,
    SIGNAL_DATA_UPDATED,
    WS_PATH,
    WS_SUBPROTOCOL,
)

from .protocol import (
    build_message,
    parse_config_response,
    parse_message,
    parse_smartroller_report,
)

_LOGGER = logging.getLogger(__name__)


class ReeffactoryCoordinator:
    """Manages the persistent WebSocket connection to a Reef Factory Roller Mat device."""

    def __init__(self, hass: HomeAssistant, host: str, name: str) -> None:
        self.hass = hass
        self.host = host
        self.name = name

        self.serial_number: str | None = None
        self.firmware_version: str = "0.0.0"

        self.data: dict = {}
        self.manual_advance_mm = 30
        
        self.roll_replacement_mode = "new"

        self.used_roll_diameter = 140
        
        self.available: bool = False

        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._session: aiohttp.ClientSession | None = None

        self._listen_task: asyncio.Task | None = None
        self._ping_task: asyncio.Task | None = None

        self._stop_event = asyncio.Event()
        self._pong_received = asyncio.Event()

        self._retry_count = 0

    @property
    def unique_id_prefix(self) -> str:
        """Return a stable unique ID prefix for entities."""
        return self.serial_number

    @property
    def device_info(self) -> dict:
        """Return device info for the HA device registry."""

        identifier = self.serial_number or self.host

        return {
            "identifiers": {
                (DOMAIN, identifier)
            },
            "name": "Reef Factory Smart Roller",
            "manufacturer": "Reef Factory",
            "model": "Smart Roller",
            "sw_version": self.firmware_version,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_start(self) -> None:
        """Start the WebSocket connection."""
        self._stop_event.clear()
        await self._connect()

    async def async_stop(self) -> None:
        """Disconnect and clean up all resources."""

        self._stop_event.set()

        for task in (self._listen_task, self._ping_task):
            if task and not task.done():
                task.cancel()

        if self._ws and not self._ws.closed and self.serial_number:
            try:
                leave_payload = self.serial_number.encode("ascii") + b"\x00"

                msg = build_message(
                    self.serial_number,
                    "pmConnect",
                    "leave",
                    payload=leave_payload,
                )

                await self._ws.send_bytes(msg)

            except Exception:
                pass

        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._session and not self._session.closed:
            await self._session.close()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    async def _close_connection(self) -> None:
        """Close existing WebSocket and session if open."""

        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()

        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._session and not self._session.closed:
            await self._session.close()

        self._ws = None
        self._session = None

    async def _connect(self) -> None:
        """Establish a WebSocket connection to the device."""

        if self._stop_event.is_set():
            return

        await self._close_connection()

        url = f"ws://{self.host}/{WS_PATH}"

        try:
            self._session = aiohttp.ClientSession()

            self._ws = await self._session.ws_connect(
                url,
                protocols=[WS_SUBPROTOCOL],
                timeout=10,
            )

            self._retry_count = 0

            _LOGGER.debug("Connected to %s", url)

            msg = build_message(
                "0000000000000000",
                "get",
                "config",
            )

            await self._ws.send_bytes(msg)

            self._listen_task = asyncio.create_task(
                self._listen()
            )

            self._ping_task = asyncio.create_task(
                self._ping_loop()
            )

        except (
            aiohttp.ClientError,
            OSError,
            asyncio.TimeoutError,
        ) as err:

            _LOGGER.warning(
                "Connection to %s failed: %s",
                self.host,
                err,
            )

            if self._session and not self._session.closed:
                await self._session.close()

            await self._schedule_reconnect()

    async def _listen(self) -> None:
        """Read incoming WebSocket messages until disconnection."""

        try:
            async for ws_msg in self._ws:

                if ws_msg.type == aiohttp.WSMsgType.BINARY:
                    self._handle_message(ws_msg.data)

                elif ws_msg.type in (
                    aiohttp.WSMsgType.ERROR,
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSING,
                    aiohttp.WSMsgType.CLOSED,
                ):
                    break

        except asyncio.CancelledError:
            return

        except Exception:
            _LOGGER.exception(
                "WebSocket listener error for %s",
                self.host,
            )

        finally:
            if not self._stop_event.is_set():
                self._set_unavailable()
                await self._cleanup_and_reconnect()

    def _set_unavailable(self) -> None:
        """Mark the device as unavailable and notify entities."""

        if self.available:
            self.available = False

            async_dispatcher_send(
                self.hass,
                SIGNAL_CONNECTION_STATE,
                False,
            )

    async def _cleanup_and_reconnect(self) -> None:
        """Close current session and schedule reconnect."""

        await self._close_connection()
        await self._schedule_reconnect()

    async def _schedule_reconnect(self) -> None:
        """Reconnect with progressive back-off."""

        if self._stop_event.is_set():
            return

        self._retry_count += 1

        if self._retry_count <= 3:
            delay = 5
        elif self._retry_count <= 10:
            delay = 15
        else:
            delay = 30

        _LOGGER.debug(
            "Reconnecting to %s in %ss (attempt %d)",
            self.host,
            delay,
            self._retry_count,
        )

        await asyncio.sleep(delay)

        if not self._stop_event.is_set():
            self.hass.async_create_task(
                self._connect()
            )

    # ------------------------------------------------------------------
    # Smart Roller commands
    # ------------------------------------------------------------------

    async def async_set_auto_mode(self, enabled: bool) -> None:
        """Set Smart Roller automatic mode."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        payload = bytearray([
            1 if enabled else 0
        ])

        identifier = str(
            int(time.time() * 1000)
        )

        msg = build_message(
            self.serial_number,
            "srSet",
            "mode",
            identifier=identifier,
            payload=payload,
        )

        _LOGGER.info(
            "TX MODE enabled=%s payload=%s ident=%s",
            enabled,
            payload.hex(),
            identifier,
        )

        await self._ws.send_bytes(msg)

    async def async_manual_advance(
        self,
        distance_mm: int,
    ) -> None:
        """Manually advance fleece roll."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        payload = b"\x00\x00\x00" + distance_mm.to_bytes(2, "little")

        _LOGGER.info(
            "TX MANUAL ADVANCE distance=%s payload=%s",
            distance_mm,
            payload.hex(),
        )

        msg = build_message(
            self.serial_number,
            "srExecute",
            "manual",
            payload=payload,
        )

        await self._ws.send_bytes(msg)
    
    async def async_unblock(
        self,
    ) -> None:
        """Clear jammed roller state."""

        if not self._ws or self._ws.closed:
            return

        import time

        identifier = str(
            int(time.time() * 1000)
        )

        payload = b"\x00\x00"

        _LOGGER.info(
            "TX UNBLOCK ident=%s payload=%s",
            identifier,
            payload.hex(),
        )

        msg = build_message(
            self.serial_number,
            "srSet",
            "unblock",
            identifier=identifier,
            payload=payload,
        )

        await self._ws.send_bytes(msg)
    
    async def async_replace_roll(
        self,
    ) -> None:
        """Replace fleece roll."""

        if not self._ws or self._ws.closed:
            return

        import time

        identifier = str(
            int(time.time() * 1000)
        )

        if (
            self.roll_replacement_mode
            == "new"
        ):

            payload = (
                b"\xff\xff\xff\xff\x00"
            )

        else:

            payload = (
                self.used_roll_diameter.to_bytes(
                    4,
                    "big",
                )
                + b"\x00"
            )

        _LOGGER.info(
            (
                "TX REPLACE ROLL "
                "mode=%s "
                "diameter=%s "
                "payload=%s"
            ),
            self.roll_replacement_mode,
            self.used_roll_diameter,
            payload.hex(),
        )

        msg = build_message(
            self.serial_number,
            "srSet",
            "newRoll",
            identifier=identifier,
            payload=payload,
        )

        await self._ws.send_bytes(msg)
    
    async def async_set_settings(
        self,
        shift_mm: int,
        delay_seconds: int,
        reminder: int,
    ) -> None:
        """Send Smart Roller settings."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        payload = bytearray(5)

        payload[0] = (shift_mm >> 8) & 0xFF
        payload[1] = shift_mm & 0xFF

        payload[2] = (delay_seconds >> 8) & 0xFF
        payload[3] = delay_seconds & 0xFF

        payload[4] = reminder & 0xFF

        msg = build_message(
            self.serial_number,
            "srSet",
            "settings",
            payload=payload,
        )

        _LOGGER.info(
            "TX SETTINGS payload=%s",
            payload.hex(),
        )

        await self._ws.send_bytes(msg)

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    @callback
    def _handle_message(self, data: bytes) -> None:
        """Parse and dispatch an incoming binary message."""

        msg = parse_message(data)

        if (
            msg.command == "refresh"
            and msg.subcommand == "config"
        ):
            self._handle_config(msg.payload)

        elif (
            msg.command == "srReport"
            and msg.subcommand == "all"
        ):
            self._handle_smartroller_report(
                msg.payload
            )

        elif msg.command == "pong":
            self._pong_received.set()

    def _handle_config(self, payload: bytes) -> None:
        """Process config response."""

        config = parse_config_response(payload)

        self.serial_number = config["serial_number"]
        self.firmware_version = config["firmware_version"]

        self.available = True

        _LOGGER.info(
            "Reef Factory device %s, firmware %s",
            self.serial_number,
            self.firmware_version,
        )

        async_dispatcher_send(
            self.hass,
            SIGNAL_CONNECTION_STATE,
            True,
        )

        self.hass.async_create_task(
            self._subscribe()
        )

    async def _subscribe(self) -> None:
        """Send Smart Roller join request."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        join_payload = (
            self.serial_number.encode("ascii")
            + b"\x00"
        )

        msg = build_message(
            self.serial_number,
            "srConnect",
            "join",
            payload=join_payload,
        )

        _LOGGER.info(
            "Sending Smart Roller join request"
        )

        await self._ws.send_bytes(msg)

    def _handle_smartroller_report(
        self,
        payload: bytes,
    ) -> None:
        """Handle Smart Roller telemetry."""

        self.data = parse_smartroller_report(
            payload
        )

        async_dispatcher_send(
            self.hass,
            SIGNAL_DATA_UPDATED,
        )

    # ------------------------------------------------------------------
    # Ping / pong
    # ------------------------------------------------------------------

    async def _ping_loop(self) -> None:
        """Send periodic pings and verify pong responses."""

        try:
            while not self._stop_event.is_set():

                await asyncio.sleep(PING_INTERVAL)

                if not self._ws or self._ws.closed:
                    break

                self._pong_received.clear()

                serial = (
                    self.serial_number
                    or "0000000000000000"
                )

                msg = build_message(
                    serial,
                    "ping",
                    "ping",
                )

                try:
                    await self._ws.send_bytes(msg)

                except Exception:

                    if self._ws and not self._ws.closed:
                        await self._ws.close()

                    break

                try:
                    await asyncio.wait_for(
                        self._pong_received.wait(),
                        timeout=PONG_TIMEOUT,
                    )

                except asyncio.TimeoutError:

                    _LOGGER.warning(
                        "Pong timeout from %s",
                        self.host,
                    )

                    if self._ws and not self._ws.closed:
                        await self._ws.close()

                    break

        except asyncio.CancelledError:
            return