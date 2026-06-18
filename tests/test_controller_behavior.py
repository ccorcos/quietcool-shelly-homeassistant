"""Behavior tests for the shared controller.

These tests use small Home Assistant stand-ins so they can run without the full
Home Assistant test harness. They lock down the relay sequencing this integration
expects: speed relay changes should not cycle master power.
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "custom_components.whole_house_fan_controller"
INTEGRATION = ROOT / "custom_components" / "whole_house_fan_controller"


def _install_homeassistant_stubs() -> None:
    """Install enough Home Assistant stubs to import the integration module."""
    modules = {
        "homeassistant": types.ModuleType("homeassistant"),
        "homeassistant.config_entries": types.ModuleType("homeassistant.config_entries"),
        "homeassistant.const": types.ModuleType("homeassistant.const"),
        "homeassistant.core": types.ModuleType("homeassistant.core"),
        "homeassistant.exceptions": types.ModuleType("homeassistant.exceptions"),
        "homeassistant.helpers": types.ModuleType("homeassistant.helpers"),
        "homeassistant.helpers.event": types.ModuleType("homeassistant.helpers.event"),
        "homeassistant.helpers.typing": types.ModuleType("homeassistant.helpers.typing"),
        "homeassistant.util": types.ModuleType("homeassistant.util"),
        "homeassistant.util.dt": types.ModuleType("homeassistant.util.dt"),
    }

    for name, module in modules.items():
        sys.modules[name] = module

    modules["homeassistant.config_entries"].ConfigEntry = object
    modules["homeassistant.const"].CONF_NAME = "name"
    modules["homeassistant.const"].STATE_ON = "on"
    modules["homeassistant.const"].Platform = types.SimpleNamespace(
        FAN="fan",
        NUMBER="number",
        BUTTON="button",
        SENSOR="sensor",
    )
    modules["homeassistant.core"].HomeAssistant = object
    modules["homeassistant.core"].callback = lambda func: func

    class HomeAssistantError(Exception):
        pass

    modules["homeassistant.exceptions"].HomeAssistantError = HomeAssistantError
    modules["homeassistant.helpers.event"].async_call_later = lambda hass, delay, action: (lambda: None)
    modules["homeassistant.helpers.event"].async_track_state_change_event = lambda *args, **kwargs: (lambda: None)
    modules["homeassistant.helpers.typing"].ConfigType = dict
    modules["homeassistant.util.dt"].utcnow = __import__("datetime").datetime.utcnow
    modules["homeassistant.util"].dt = modules["homeassistant.util.dt"]


def _load_integration_module():
    """Load the integration module with Home Assistant stubs installed."""
    _install_homeassistant_stubs()

    for name in list(sys.modules):
        if name == PACKAGE or name.startswith(f"{PACKAGE}."):
            del sys.modules[name]

    spec = importlib.util.spec_from_file_location(
        PACKAGE,
        INTEGRATION / "__init__.py",
        submodule_search_locations=[str(INTEGRATION)],
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE] = module
    spec.loader.exec_module(module)
    return module


class FakeState:
    """Minimal HA state object."""

    def __init__(self, state: str) -> None:
        self.state = state


class FakeStates:
    """Minimal HA states registry."""

    def __init__(self) -> None:
        self._states = {
            "switch.whf_power": FakeState("off"),
            "switch.whf_speed_a": FakeState("off"),
            "switch.whf_speed_b": FakeState("off"),
        }

    def get(self, entity_id: str) -> FakeState | None:
        return self._states.get(entity_id)

    def set(self, entity_id: str, state: str) -> None:
        self._states[entity_id] = FakeState(state)


class FakeServices:
    """Capture switch service calls and update fake state."""

    def __init__(self, states: FakeStates) -> None:
        self.states = states
        self.calls: list[tuple[str, str, str, bool]] = []

    async def async_call(self, domain: str, service: str, data: dict[str, Any], *, blocking: bool) -> None:
        entity_id = data["entity_id"]
        self.calls.append((domain, service, entity_id, blocking))
        self.states.set(entity_id, "on" if service == "turn_on" else "off")


class FakeHass:
    """Minimal Home Assistant object used by the controller."""

    def __init__(self) -> None:
        self.states = FakeStates()
        self.services = FakeServices(self.states)

    def async_create_task(self, coro):
        return asyncio.create_task(coro)


class FakeEntry:
    """Minimal config entry."""

    entry_id = "test_entry"
    options: dict[str, Any] = {}
    data = {
        "name": "Whole House Fan",
        "power_switch_entity": "switch.whf_power",
        "speed_relay_a_entity": "switch.whf_speed_a",
        "speed_relay_b_entity": "switch.whf_speed_b",
        "speed_map": {
            "Low": {"relay_a": False, "relay_b": False},
            "Medium": {"relay_a": True, "relay_b": False},
            "High": {"relay_a": True, "relay_b": True},
        },
        "default_run_hours": 4.0,
        "min_run_hours": 0.5,
        "max_run_hours": 12.0,
        "run_hours_step": 0.5,
    }


def _make_controller():
    module = _load_integration_module()
    hass = FakeHass()
    controller = module.WholeHouseFanController(hass, FakeEntry())
    return controller, hass


def test_turn_on_applies_speed_before_master_power() -> None:
    controller, hass = _make_controller()
    controller.current_preset = "Medium"

    asyncio.run(controller.async_turn_on())

    assert hass.services.calls == [
        ("switch", "turn_on", "switch.whf_speed_a", True),
        ("switch", "turn_off", "switch.whf_speed_b", True),
        ("switch", "turn_on", "switch.whf_power", True),
    ]


def test_speed_change_while_running_does_not_cycle_master_power() -> None:
    controller, hass = _make_controller()
    hass.states.set("switch.whf_power", "on")

    asyncio.run(controller.async_set_preset_mode("High"))

    assert hass.services.calls == [
        ("switch", "turn_on", "switch.whf_speed_a", True),
        ("switch", "turn_on", "switch.whf_speed_b", True),
    ]
    assert hass.states.get("switch.whf_power").state == "on"


def test_turn_off_only_turns_off_master_power() -> None:
    controller, hass = _make_controller()
    hass.states.set("switch.whf_power", "on")
    hass.states.set("switch.whf_speed_a", "on")
    hass.states.set("switch.whf_speed_b", "on")

    asyncio.run(controller.async_turn_off())

    assert hass.services.calls == [("switch", "turn_off", "switch.whf_power", True)]
    assert hass.states.get("switch.whf_speed_a").state == "on"
    assert hass.states.get("switch.whf_speed_b").state == "on"
