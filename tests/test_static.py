"""Static repository checks."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "whole_house_fan_controller"
REPO_URL = "https://github.com/ccorcos/quietcool-shelly-homeassistant"
DOMAIN = "whole_house_fan_controller"


def test_manifest_metadata() -> None:
    """Manifest points at the expected integration and repository."""
    manifest = json.loads((INTEGRATION / "manifest.json").read_text())

    assert manifest["domain"] == DOMAIN
    assert manifest["documentation"] == REPO_URL
    assert manifest["issue_tracker"] == f"{REPO_URL}/issues"
    assert manifest["config_flow"] is True


def test_hacs_metadata() -> None:
    """HACS metadata includes the platforms exposed by the integration."""
    hacs = json.loads((ROOT / "hacs.json").read_text())

    assert hacs["name"] == "QuietCool Shelly House Fan Controller"
    assert hacs["content_in_root"] is False
    assert set(hacs["domains"]) == {"fan", "number", "button", "sensor", "switch"}


def test_translation_files_are_valid_and_in_sync() -> None:
    """Base strings and English translations should stay in sync."""
    strings = json.loads((INTEGRATION / "strings.json").read_text())
    english = json.loads((INTEGRATION / "translations" / "en.json").read_text())

    assert english == strings


def test_delay_options_were_removed() -> None:
    """Delay/interlock settings should not reappear in user-facing config."""
    forbidden = {"power_off_delay", "speed_settle_delay", "invalid_delay"}
    for path in [
        INTEGRATION / "const.py",
        INTEGRATION / "config_flow.py",
        INTEGRATION / "strings.json",
        INTEGRATION / "translations" / "en.json",
    ]:
        text = path.read_text()
        for token in forbidden:
            assert token not in text


def test_readme_documents_target_hardware_and_repo_url() -> None:
    """README should mention the intended hardware and current repo URL."""
    readme = (ROOT / "README.md").read_text()

    assert REPO_URL in readme
    assert "Shelly 1 Gen 4" in readme
    assert "PACKARD PR372 Fan Relay" in readme
    assert "## Troubleshooting" not in readme
