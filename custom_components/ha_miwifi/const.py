"""Constants for the MiWiFi integration."""

from __future__ import annotations

DOMAIN = "ha_miwifi"

CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CONSIDER_HOME = "consider_home"
CONF_EXCLUDED_MACS = "excluded_macs"

DEFAULT_NAME = "MiWiFi"
DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 600
DEFAULT_CONSIDER_HOME = 180

MANUFACTURER = "Xiaomi"

EVENT_DEVICE_CONNECTED = "ha_miwifi_device_connected"
EVENT_DEVICE_DISCONNECTED = "ha_miwifi_device_disconnected"
EVENT_NEW_DEVICE = "ha_miwifi_new_device"

ATTR_ENTRY_ID = "entry_id"

SERVICE_ADD_RESERVATION = "add_dhcp_reservation"
SERVICE_REMOVE_RESERVATION = "remove_dhcp_reservation"
SERVICE_BLOCK_DEVICE = "block_device"
SERVICE_UNBLOCK_DEVICE = "unblock_device"
SERVICE_LUCI_REQUEST = "luci_request"
SERVICE_RUN_SPEED_TEST = "run_speed_test"
SERVICE_ADD_PORT_FORWARD = "add_port_forward"
SERVICE_DELETE_PORT_FORWARD = "delete_port_forward"
SERVICE_SET_DMZ = "set_dmz"
SERVICE_CLEAR_DMZ = "clear_dmz"
SERVICE_SET_DDNS = "set_ddns"
