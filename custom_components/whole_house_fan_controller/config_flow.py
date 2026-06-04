"""Config flow for Whole House Fan Controller."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    CONF_DEFAULT_RUN_HOURS,
    CONF_HIGH_RELAY_A,
    CONF_HIGH_RELAY_B,
    CONF_LOW_RELAY_A,
    CONF_LOW_RELAY_B,
    CONF_MAX_RUN_HOURS,
    CONF_MEDIUM_RELAY_A,
    CONF_MEDIUM_RELAY_B,
    CONF_MIN_RUN_HOURS,
    CONF_POWER_OFF_DELAY,
    CONF_POWER_SWITCH,
    CONF_RUN_HOURS_STEP,
    CONF_SPEED_MAP,
    CONF_SPEED_RELAY_A,
    CONF_SPEED_RELAY_B,
    CONF_SPEED_SETTLE_DELAY,
    DEFAULT_MAX_RUN_HOURS,
    DEFAULT_MIN_RUN_HOURS,
    DEFAULT_NAME,
    DEFAULT_POWER_OFF_DELAY,
    DEFAULT_RUN_HOURS,
    DEFAULT_RUN_HOURS_STEP,
    DEFAULT_SPEED_MAP,
    DEFAULT_SPEED_SETTLE_DELAY,
    DOMAIN,
    PRESET_HIGH,
    PRESET_LOW,
    PRESET_MEDIUM,
    PRESET_MODES,
)


def _switch_selector() -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain="switch"))


def _required_with_optional_default(key: str, defaults: dict[str, Any]) -> vol.Required:
    """Return a required schema marker, only setting a default when one exists."""
    if key in defaults:
        return vol.Required(key, default=defaults[key])
    return vol.Required(key)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    speed_map = defaults.get(CONF_SPEED_MAP, DEFAULT_SPEED_MAP)
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            _required_with_optional_default(CONF_POWER_SWITCH, defaults): _switch_selector(),
            _required_with_optional_default(CONF_SPEED_RELAY_A, defaults): _switch_selector(),
            _required_with_optional_default(CONF_SPEED_RELAY_B, defaults): _switch_selector(),
            vol.Required(CONF_LOW_RELAY_A, default=speed_map[PRESET_LOW]["relay_a"]): bool,
            vol.Required(CONF_LOW_RELAY_B, default=speed_map[PRESET_LOW]["relay_b"]): bool,
            vol.Required(CONF_MEDIUM_RELAY_A, default=speed_map[PRESET_MEDIUM]["relay_a"]): bool,
            vol.Required(CONF_MEDIUM_RELAY_B, default=speed_map[PRESET_MEDIUM]["relay_b"]): bool,
            vol.Required(CONF_HIGH_RELAY_A, default=speed_map[PRESET_HIGH]["relay_a"]): bool,
            vol.Required(CONF_HIGH_RELAY_B, default=speed_map[PRESET_HIGH]["relay_b"]): bool,
            vol.Required(CONF_POWER_OFF_DELAY, default=defaults.get(CONF_POWER_OFF_DELAY, DEFAULT_POWER_OFF_DELAY)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_SPEED_SETTLE_DELAY, default=defaults.get(CONF_SPEED_SETTLE_DELAY, DEFAULT_SPEED_SETTLE_DELAY)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_DEFAULT_RUN_HOURS, default=defaults.get(CONF_DEFAULT_RUN_HOURS, DEFAULT_RUN_HOURS)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.1, max=24, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_MIN_RUN_HOURS, default=defaults.get(CONF_MIN_RUN_HOURS, DEFAULT_MIN_RUN_HOURS)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.1, max=24, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_MAX_RUN_HOURS, default=defaults.get(CONF_MAX_RUN_HOURS, DEFAULT_MAX_RUN_HOURS)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.1, max=24, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_RUN_HOURS_STEP, default=defaults.get(CONF_RUN_HOURS_STEP, DEFAULT_RUN_HOURS_STEP)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0.1, max=6, step=0.1, mode=selector.NumberSelectorMode.BOX)
            ),
        }
    )


def _normalize_user_input(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_NAME: user_input[CONF_NAME],
        CONF_POWER_SWITCH: user_input[CONF_POWER_SWITCH],
        CONF_SPEED_RELAY_A: user_input[CONF_SPEED_RELAY_A],
        CONF_SPEED_RELAY_B: user_input[CONF_SPEED_RELAY_B],
        CONF_SPEED_MAP: {
            PRESET_LOW: {
                "relay_a": user_input[CONF_LOW_RELAY_A],
                "relay_b": user_input[CONF_LOW_RELAY_B],
            },
            PRESET_MEDIUM: {
                "relay_a": user_input[CONF_MEDIUM_RELAY_A],
                "relay_b": user_input[CONF_MEDIUM_RELAY_B],
            },
            PRESET_HIGH: {
                "relay_a": user_input[CONF_HIGH_RELAY_A],
                "relay_b": user_input[CONF_HIGH_RELAY_B],
            },
        },
        CONF_POWER_OFF_DELAY: float(user_input[CONF_POWER_OFF_DELAY]),
        CONF_SPEED_SETTLE_DELAY: float(user_input[CONF_SPEED_SETTLE_DELAY]),
        CONF_DEFAULT_RUN_HOURS: float(user_input[CONF_DEFAULT_RUN_HOURS]),
        CONF_MIN_RUN_HOURS: float(user_input[CONF_MIN_RUN_HOURS]),
        CONF_MAX_RUN_HOURS: float(user_input[CONF_MAX_RUN_HOURS]),
        CONF_RUN_HOURS_STEP: float(user_input[CONF_RUN_HOURS_STEP]),
    }


def _speed_map_has_all_presets(speed_map: dict[str, Any]) -> bool:
    return set(speed_map) == set(PRESET_MODES)


async def _validate(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    entities = [data[CONF_POWER_SWITCH], data[CONF_SPEED_RELAY_A], data[CONF_SPEED_RELAY_B]]
    if len(set(entities)) != len(entities):
        errors["base"] = "duplicate_entities"

    registry = async_get_entity_registry(hass)
    for key in (CONF_POWER_SWITCH, CONF_SPEED_RELAY_A, CONF_SPEED_RELAY_B):
        entity_id = data[key]
        if not isinstance(entity_id, str) or not entity_id.startswith("switch."):
            errors[key] = "not_switch"
            continue
        if hass.states.get(entity_id) is None and registry.async_get(entity_id) is None:
            errors[key] = "entity_not_found"

    if not _speed_map_has_all_presets(data[CONF_SPEED_MAP]):
        errors["base"] = "invalid_speed_map"

    if data[CONF_POWER_OFF_DELAY] < 0 or data[CONF_SPEED_SETTLE_DELAY] < 0:
        errors["base"] = "invalid_delay"

    min_hours = data[CONF_MIN_RUN_HOURS]
    max_hours = data[CONF_MAX_RUN_HOURS]
    default_hours = data[CONF_DEFAULT_RUN_HOURS]
    step = data[CONF_RUN_HOURS_STEP]
    if min_hours <= 0 or max_hours <= 0 or step <= 0:
        errors["base"] = "invalid_timer_range"
    elif min_hours > max_hours:
        errors[CONF_MIN_RUN_HOURS] = "min_greater_than_max"
    elif not min_hours <= default_hours <= max_hours:
        errors[CONF_DEFAULT_RUN_HOURS] = "default_out_of_range"

    return errors


class WholeHouseFanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _normalize_user_input(user_input)
            errors = await _validate(self.hass, data)
            if not errors:
                await self.async_set_unique_id(data[CONF_POWER_SWITCH])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=data[CONF_NAME], data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input or {}),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create options flow."""
        return WholeHouseFanOptionsFlow(config_entry)


class WholeHouseFanOptionsFlow(config_entries.OptionsFlow):
    """Handle options for an existing config entry."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        errors: dict[str, str] = {}
        defaults = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            data = _normalize_user_input(user_input)
            errors = await _validate(self.hass, data)
            if not errors:
                return self.async_create_entry(title="", data=data)

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(user_input or defaults),
            errors=errors,
        )
