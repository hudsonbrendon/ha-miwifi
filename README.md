<p align="center">
  <img src="custom_components/ha_miwifi/brand/logo@2x.png" alt="MiWiFi" height="128">
</p>

# MiWiFi for Home Assistant

[![Tests](https://github.com/hudsonbrendon/ha-miwifi/actions/workflows/tests.yml/badge.svg)](https://github.com/hudsonbrendon/ha-miwifi/actions/workflows/tests.yml)
[![Hassfest](https://github.com/hudsonbrendon/ha-miwifi/actions/workflows/hassfest.yml/badge.svg)](https://github.com/hudsonbrendon/ha-miwifi/actions/workflows/hassfest.yml)
[![HACS](https://github.com/hudsonbrendon/ha-miwifi/actions/workflows/validate.yml/badge.svg)](https://github.com/hudsonbrendon/ha-miwifi/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/hudsonbrendon/ha-miwifi?sort=semver)](https://github.com/hudsonbrendon/ha-miwifi/releases)
[![Downloads](https://img.shields.io/github/downloads/hudsonbrendon/ha-miwifi/total)](https://github.com/hudsonbrendon/ha-miwifi/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.12.0%2B-18BCF2?logo=homeassistant&logoColor=white)](https://www.home-assistant.io/)
[![License](https://img.shields.io/github/license/hudsonbrendon/ha-miwifi)](LICENSE)

Monitor and control **Xiaomi / MiWiFi routers** in Home Assistant over the local LuCI HTTP API. Mesh-aware: add each router as its own entry and the gateway auto-discovers and links its mesh peers. Powered by [`python-xiaomi-miwifi`](https://github.com/hudsonbrendon/python-xiaomi-miwifi).

## Features

- 📊 Sensors: connected devices, per-band client counts, download/upload speed, WAN IP, WAN connected-since, WAN total download/upload, WAN max speeds, WAN type, WAN gateway, 2.4/5 GHz channel, firmware, mesh node count, operating mode, Ethernet ports connected, speed-test download/upload, WAN DNS, port-forwarding rule count, DHCP lease time, timezone
- 🔌 Binary sensors: WAN link, status LED, DMZ, DDNS, IPv6
- 🆕 Firmware update entity (install/latest/changelog)
- 📡 Device tracker: presence for every device seen on the network, with per-client signal, band and traffic attributes, plus `signal_quality` and `last_seen`
- 🔔 Device events + automation triggers: connected, disconnected, and new-device
- 🩺 System Health panel (router count, reachability, firmware, devices, mesh nodes)
- 🛠️ Repairs: firmware-update-available and unsupported-router issues
- 🔑 Reauthentication and reconfigure flows
- ⚙️ Advanced options: consider-home debounce and MAC exclusion list
- 🕸️ Per-router entries with automatic mesh discovery and `via_device` correlation
- 🎚️ Selects: 2.4/5 GHz Wi-Fi channel and signal strength (transmit power)
- 🛠️ Controls: 2.4/5 GHz radio switches, QoS switch, reboot button, run-speed-test button
- 🌍 Country-code diagnostic sensor and a full ~45-model supported-router table (incl. RC06 and RD03)
- ⚙️ Services: `add_dhcp_reservation`, `remove_dhcp_reservation`, `block_device`, `unblock_device`, `luci_request`, `run_speed_test`, `add_port_forward`, `delete_port_forward`, `set_dmz`, `clear_dmz`, `set_ddns`
- 🌐 English + Portuguese (pt-BR) translations
- 🎨 Native brand icons (no home-assistant/brands PR required)

## Installation (HACS)

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hudsonbrendon&repository=ha-miwifi&category=integration)
[![Add integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ha_miwifi)

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/hudsonbrendon/ha-miwifi`, category **Integration**.
2. Install **MiWiFi**, restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → MiWiFi**.
4. Enter the router host (e.g. `192.168.31.1`) and admin password.

## Entities

| Entity | Platform | Notes |
|--------|----------|-------|
| Connected devices | sensor | total LAN clients |
| 2.4 GHz / 5 GHz clients | sensor | per-band counts |
| Download / Upload speed | sensor | aggregate B/s |
| WAN IP | sensor | public IP |
| WAN connected since | sensor | timestamp, diagnostic |
| WAN download / upload total | sensor | cumulative bytes |
| WAN max download / upload speed | sensor | peak B/s |
| WAN type | sensor | e.g. `dhcp`, diagnostic |
| WAN gateway | sensor | diagnostic |
| 2.4 GHz / 5 GHz channel | sensor | diagnostic |
| Firmware version | sensor | diagnostic |
| Operating mode | sensor | router/repeater/AP/mesh, diagnostic |
| Ethernet ports connected | sensor | count of linked LAN ports, diagnostic |
| Country code | sensor | regulatory region, diagnostic |
| Speed test download / upload | sensor | last on-device WAN speed test (Mbit/s) |
| WAN DNS | sensor | WAN-side DNS servers, diagnostic |
| Port forwarding rules | sensor | active single-port forward count, diagnostic |
| DHCP lease time | sensor | minutes, diagnostic |
| Timezone | sensor | router timezone, diagnostic |
| Mesh nodes | sensor | leaf count |
| Firmware | update | install/latest/changelog |
| Presence | device_tracker | one per device seen; tracks all seen devices; exposes `signal`, `band`, `download_speed`, `upload_speed`, `download_total`, `upload_total`, `signal_quality`, `last_seen` attributes; honours the consider-home debounce |
| WAN link | binary_sensor | connectivity |
| Status LED | binary_sensor | LED state |
| DMZ | binary_sensor | DMZ enabled, diagnostic |
| DDNS | binary_sensor | DDNS enabled, diagnostic |
| IPv6 | binary_sensor | IPv6 enabled on WAN, diagnostic |
| 2.4 GHz / 5 GHz channel | select | ⚠️ disruptive (restarts the radio) |
| 2.4 GHz / 5 GHz signal strength | select | max/mid/min, ⚠️ disruptive |
| 2.4 GHz / 5 GHz Wi-Fi | switch | ⚠️ disruptive |
| QoS | switch | smart bandwidth limiting |
| Reboot | button | ⚠️ disruptive |
| Run speed test | button | triggers an on-device WAN speed test |

## Services

- `ha_miwifi.add_dhcp_reservation` — reserve an IP for a MAC.
- `ha_miwifi.remove_dhcp_reservation` — remove a reservation.
- `ha_miwifi.block_device` — block a device from the network by MAC.
- `ha_miwifi.unblock_device` — unblock a previously blocked device by MAC.
- `ha_miwifi.luci_request` — perform a read-only GET to any MiWiFi LuCI API path and return the JSON response (e.g. `api/misystem/router_info`).
- `ha_miwifi.run_speed_test` — trigger an on-device WAN speed test (briefly saturates the link).
- `ha_miwifi.add_port_forward` — add a single-port forwarding rule (ip, name, proto, source_port, dest_port).
- `ha_miwifi.delete_port_forward` — delete a port forwarding rule by its external (source) port.
- `ha_miwifi.set_dmz` — forward all unmatched WAN traffic to a single LAN host.
- `ha_miwifi.clear_dmz` — disable DMZ forwarding.
- `ha_miwifi.set_ddns` — enable or disable dynamic DNS.

## Events & automation triggers

The integration fires bus events as devices come and go, and exposes matching device-automation triggers:

| Event | Trigger | Payload |
|-------|---------|---------|
| `ha_miwifi_device_connected` | A device connected | `mac`, `name`, `ip` |
| `ha_miwifi_device_disconnected` | A device disconnected | `mac` |
| `ha_miwifi_new_device` | A new device joined | `mac`, `name`, `ip` |

## Multiple routers & mesh discovery

Each router is added as its own config entry with its own full set of entities. To add a mesh, set up the gateway first: the integration reads its mesh topology and automatically surfaces every peer node as a discovery flow ready to add. Peers also show up on their own when they appear on the network via DHCP. Because discovery reuses the admin passwords already stored on your other entries, adding a peer usually needs no extra input.

Discovered peers are linked under their gateway via `via_device`, so the device hierarchy in Home Assistant mirrors your physical mesh.

> **Breaking change (0.7.0):** mesh nodes are no longer exposed as per-leaf child sensors under the gateway entry — each router is now its own entry. Entries are also keyed by router MAC instead of host; existing entries are migrated automatically on upgrade.

## System Health & Repairs

- **System Health** (Settings → System → Repairs → System information) shows router count, reachability, firmware version, connected devices, and mesh nodes.
- **Repairs** raises informational issues when a firmware update is available or when the router model is not in the supported table.

## Reauthentication & reconfigure

- If the router rejects the stored password, Home Assistant starts a **reauthentication** flow to enter the current password.
- The **reconfigure** option (integration ⋮ menu) lets you change the router host and password without removing the entry.

## Options

Open the integration's **Configure** dialog to set:

- **Update interval** (seconds) — polling cadence.
- **Consider-home** (seconds) — how long a device is still reported home after it stops responding.
- **Excluded MACs** — comma-separated MAC addresses to ignore for presence and events.

## Supported routers

These hardware codes are recognized with friendly names; any unlisted model still works with a generic name (open an issue to add yours).

| Hardware | Model |
|----------|-------|
| R1D | Xiaomi Mi Router R1D |
| R2D | Xiaomi Mi Router R2D |
| R3 | Xiaomi Mi Router 3 |
| R3G | Xiaomi Mi Router 3G |
| R3P | Xiaomi Mi Router 3 Pro |
| R3D | Xiaomi Mi Router HD |
| R3L | Xiaomi Mi Router 3C |
| R3A | Xiaomi Mi Router 3A |
| R4 | Xiaomi Mi Router 4 |
| R4C / R4CM | Xiaomi Mi Router 4C |
| R4A / R4AC | Xiaomi Mi Router 4A |
| R4AV2 | Xiaomi Mi Router 4A v2 |
| D01 | Xiaomi Mi Router Mesh |
| R2100 | Xiaomi Mi Router AC2100 |
| RM2100 | Redmi Router AC2100 |
| R3600 | Xiaomi AIoT Router AX3600 |
| RM1800 | Xiaomi Router AX1800 |
| RA67 | Redmi Router AX5 |
| R2350 | Xiaomi Mi AIoT Router AC2350 |
| R1350 | Xiaomi Mi Router 4 Pro |
| RA69 | Redmi Router AX6 |
| RA72 | Xiaomi Router AX6000 |
| RA50 | Redmi Router AX5400 |
| RA70 | Xiaomi Router AX9000 |
| CR6606 | Xiaomi Router CR6606 |
| RA81 | Redmi Router AX3000 |
| RA80 | Xiaomi Router AX3000 |
| RB03 | Redmi Router AX6000 |
| RA71 | Redmi Router AX1800 |
| RB01 | Xiaomi Router BE7000 |
| RA82 / RB06 | Xiaomi Router AX3000T |
| CR8808 | Xiaomi Router CR8808 |
| RB02 | Redmi Router BE5000 |
| RB04 | Xiaomi Router BE3600 |
| RA74 | Xiaomi Mesh System AX3000 |
| RB08 | Xiaomi Router BE3600 2.5G |
| CB0401 | Xiaomi 5G CPE Pro |
| RC06 | Redmi Router AX6000 |
| RD03 | Xiaomi Router AX3000T NE |

## Development

```bash
uv venv && uv pip install -r requirements_test.txt
pytest && ruff check .
```

## License

MIT © Hudson Brendon
