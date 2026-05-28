# Reef Factory Smart Roller

Home Assistant integration for the Reef Factory Smart Roller fleece filter.

This integration provides fully local control and monitoring of the Reef Factory Smart Roller directly within Home Assistant, without reliance on the Reef Factory cloud platform.

---

## Features

* Fully local websocket communication
* Automatic advance control
* Manual fleece advance
* Adjustable shift length
* Adjustable advance delay
* Roll replacement support

  * New roll reset
  * Used roll diameter support
* Jam detection and recovery
* Remaining fleece tracking
* Daily usage statistics
* Automatic reconnect handling
* Native Home Assistant entities
* HACS compatible

---

## Installation

### HACS (Custom Repository)

1. Open HACS

2. Go to:
   `HACS → Integrations → ⋮ → Custom repositories`

3. Add:

   `https://github.com/downerhouse/ha-reef-factory-smartroller`

4. Category:
   `Integration`

5. Restart Home Assistant

6. Install "Reef Factory Smart Roller" from HACS

7. Restart Home Assistant again

8. Add the integration via:

   `Settings → Devices & Services → Add Integration`

---

### Manual Installation

Copy:

`custom_components/reef_factory_smartroller`

into:

`config/custom_components/`

Then restart Home Assistant.

---

## Supported Entities

### Sensors

* Remaining fleece
* Daily fleece usage
* Daily average usage
* Roller status
* Automatic mode state

### Controls

* Automatic advance enable/disable
* Manual fleece advance
* Shift length selection
* Advance delay selection
* Roll replacement mode
* Used roll diameter
* Jam recovery / restart

---

## Requirements

* Reef Factory Smart Roller
* Home Assistant 2024.1 or newer
* Local network access to the Smart Roller

---

## Screenshots

(Add screenshots here)

---

## Credits

This integration was originally inspired by and partially based on the excellent work by Dominik Hartl:

https://github.com/dominikhartl/ha-reeffactory-ph

The Smart Roller integration has since been extensively redesigned and expanded with native Smart Roller protocol support, telemetry parsing, manual advance control, jam detection and recovery, and roll replacement functionality.

The integration aims to replicate the core functionality of the official Reef Factory application entirely within Home Assistant, enabling fully local operation without reliance on the Reef Factory cloud platform.

---

## Disclaimer

This project is unofficial and is not affiliated with or endorsed by Reef Factory.

Use at your own risk.

---

## Future Plans

Potential future improvements include:

* Additional Reef Factory device support
* Diagnostics export
* Enhanced statistics
* Firmware/version diagnostics
* Expanded Home Assistant service support
