"""Binary protocol encoder/decoder for Reef Factory Smart Roller

Wire format (both directions):
    [serialNumber\\0][command\\0][subcommand\\0][identifier\\0][payload_bytes]

All string fields are ASCII, null-terminated. Payload is raw binary.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
_LOGGER = logging.getLogger(__name__)

@dataclass
class ReeffactoryMessage:
    """Parsed Reef Factory websocket message."""

    serial_number: str
    command: str
    subcommand: str
    identifier: str
    payload: bytes

@dataclass
class SmartRollerSettings:
    auto_enabled: bool
    shift_mm: int
    delay_value_1: int
    delay_value_2: int
    raw_payload: bytes

def parse_message(data: bytes) -> ReeffactoryMessage:
    """Parse a binary WebSocket frame into its string fields + payload."""
    pos = 0
    fields: list[str] = []
    for _ in range(4):
        chars: list[str] = []
        while pos < len(data):
            byte = data[pos]
            pos += 1
            if byte == 0:
                break
            chars.append(chr(byte))
        fields.append("".join(chars))

    return ReeffactoryMessage(
        serial_number=fields[0],
        command=fields[1],
        subcommand=fields[2],
        identifier=fields[3],
        payload=data[pos:],
    )


def parse_config_response(payload: bytes) -> dict[str, str]:
    """Extract serial number and firmware version from a refresh/config payload.

    Layout:
        Null-terminated serial number string
        1 byte language
        1 byte onboarding
        5 bytes firmware version string (e.g. "1.0.1")
    """
    pos = 0
    serial_chars: list[str] = []
    while pos < len(payload):
        b = payload[pos]
        pos += 1
        if b == 0:
            break
        serial_chars.append(chr(b))
    serial = "".join(serial_chars)

    pos += 1  # language byte
    pos += 1  # onboarding byte

    fw_chars: list[str] = []
    for _ in range(5):
        if pos < len(payload):
            fw_chars.append(chr(payload[pos]))
            pos += 1
    firmware = "".join(fw_chars)

    return {
        "serial_number": serial,
        "firmware_version": firmware,
    }


def build_message(
    serial_number: str,
    command: str,
    subcommand: str = "",
    identifier: str = "",
    payload: bytes | None = None,
) -> bytes:
    """Construct an outgoing binary WebSocket frame."""
    parts = bytearray()
    for field in (serial_number, command, subcommand, identifier):
        parts.extend(field.encode("ascii"))
        parts.append(0)
    if payload:
        parts.extend(payload)
    return bytes(parts)


def parse_smartroller_report(payload: bytes) -> dict:
    """Parse Smart Roller telemetry payload."""

    _LOGGER.warning(
        payload[0],
        payload[1],
        payload[2],
        payload[3],
        payload[4],
        payload[5],
        payload[6],
        payload[7],
    )

    roller_status = (
        "Jammed"
        if payload[0] == 2
        else "OK"
    )

    auto_enabled = payload[0] == 1

    shift_mm = int.from_bytes(payload[1:3], "big")
    
    reminder = payload[3]

    delay_seconds = int.from_bytes(payload[4:6], "big")

    remaining_mm = int.from_bytes(payload[10:14], "big")

    total_roll_mm = int.from_bytes(payload[14:18], "big")

    today_mm = int.from_bytes(payload[22:26], "big")

    daily_average_mm = int.from_bytes(payload[26:30], "big")

    raw_payload = payload

    return {
        "roller_status": roller_status,
        "auto_enabled": auto_enabled,
        "shift_mm": shift_mm,
        "reminder": reminder,
        "delay_seconds": delay_seconds,
        "remaining_mm": remaining_mm,
        "total_roll_mm": total_roll_mm,
        "today_mm": today_mm,
        "daily_average_mm": daily_average_mm,
        "raw_hex": payload.hex(),
        "raw_payload": raw_payload,
    }