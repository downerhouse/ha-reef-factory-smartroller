"""Constants for the Reef Factory Roller Mat integration."""

DOMAIN = "reef_factory_smartroller"
PLATFORMS = [
    "sensor",
    "switch",
    "select",
    "button",
    "number",
]

WS_PATH = "controler"
WS_SUBPROTOCOL = "arduino"

PING_INTERVAL = 30  # seconds
PONG_TIMEOUT = 10  # seconds

SIGNAL_DATA_UPDATED = f"{DOMAIN}_data_updated"
SIGNAL_CONNECTION_STATE = f"{DOMAIN}_connection_state"
