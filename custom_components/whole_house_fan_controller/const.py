"""Constants for the Whole House Fan Controller integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "whole_house_fan_controller"

CONF_POWER_SWITCH: Final = "power_switch_entity"
CONF_SPEED_RELAY_A: Final = "speed_relay_a_entity"
CONF_SPEED_RELAY_B: Final = "speed_relay_b_entity"
CONF_SPEED_MAP: Final = "speed_map"
CONF_DEFAULT_RUN_HOURS: Final = "default_run_hours"
CONF_MIN_RUN_HOURS: Final = "min_run_hours"
CONF_MAX_RUN_HOURS: Final = "max_run_hours"
CONF_RUN_HOURS_STEP: Final = "run_hours_step"

CONF_LOW_RELAY_A: Final = "low_relay_a"
CONF_LOW_RELAY_B: Final = "low_relay_b"
CONF_MEDIUM_RELAY_A: Final = "medium_relay_a"
CONF_MEDIUM_RELAY_B: Final = "medium_relay_b"
CONF_HIGH_RELAY_A: Final = "high_relay_a"
CONF_HIGH_RELAY_B: Final = "high_relay_b"

PRESET_LOW: Final = "Low"
PRESET_MEDIUM: Final = "Medium"
PRESET_HIGH: Final = "High"
PRESET_MODES: Final = [PRESET_LOW, PRESET_MEDIUM, PRESET_HIGH]

DEFAULT_NAME: Final = "Whole House Fan"
DEFAULT_RUN_HOURS: Final = 4.0
DEFAULT_MIN_RUN_HOURS: Final = 0.5
DEFAULT_MAX_RUN_HOURS: Final = 12.0
DEFAULT_RUN_HOURS_STEP: Final = 0.5

DEFAULT_SPEED_MAP: Final = {
    PRESET_LOW: {"relay_a": False, "relay_b": False},
    PRESET_MEDIUM: {"relay_a": True, "relay_b": False},
    PRESET_HIGH: {"relay_a": True, "relay_b": True},
}

DATA_SERVICES_REGISTERED: Final = "services_registered"
