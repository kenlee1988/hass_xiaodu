"""Tests for the appliance-type classification logic.

These tests cover ``ApplianceTypes`` directly. That module is pure Python with
no Home Assistant imports, so we load it by file path to avoid importing the
package ``__init__`` (which pulls in homeassistant). The test therefore runs
even without a full Home Assistant test environment.
"""
import importlib.util
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "xiaodu"
    / "ApplianceTypes.py"
)


def _load_appliance_types():
    spec = importlib.util.spec_from_file_location("xiaodu_appliance_types", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ApplianceTypes


ApplianceTypes = _load_appliance_types()


@pytest.fixture
def at():
    return ApplianceTypes()


# (appliance_type, checker_name) — the platform that SHOULD claim the device.
# This documents the current, intended routing of each XiaoDu appliance type.
@pytest.mark.parametrize(
    "appliance_type, checker",
    [
        ("LIGHT", "is_light"),
        ("CURTAIN", "is_cover"),
        ("AIR_CONDITION", "is_climate"),
        ("DOOR_LOCK", "is_lock"),
        ("SOCKET", "is_switch"),
        ("SWITCH", "is_switch"),
        ("WASHING_MACHINE", "is_switch"),
        ("WINDOW_OPENER", "is_switch"),
        # 地暖 / 新风 are intentionally routed to SWITCH (on/off only) — see
        # the design decision in the integration; not climate.
        ("HEATER", "is_switch"),
        ("AIR_FRESHER", "is_switch"),
    ],
)
def test_type_is_claimed_by_expected_checker(at, appliance_type, checker):
    assert getattr(at, checker)([appliance_type]) is True


def test_air_condition_is_climate_not_switch(at):
    """空调 must be a climate device, never a switch."""
    assert at.is_climate(["AIR_CONDITION"]) is True
    assert at.is_switch(["AIR_CONDITION"]) is False


def test_heater_and_air_fresher_are_switch_not_climate(at):
    """地暖/新风 stay as switches (only on/off), not climate."""
    for t in ("HEATER", "AIR_FRESHER"):
        assert at.is_switch([t]) is True
        assert at.is_climate([t]) is False


def test_clothes_rack_is_both_switch_and_button(at):
    """晾衣架 is deliberately registered on both SWITCH and BUTTON platforms."""
    assert at.is_switch(["CLOTHES_RACK"]) is True
    assert at.is_button(["CLOTHES_RACK"]) is True


def test_unknown_type_is_unclaimed(at):
    """A type no checker knows about must fall through every platform.

    This is exactly why 空调 disappeared: its real reported type string did not
    match 'AIR_CONDITION'. Once the real string is known, add it to CLIMATE().
    """
    unknown = ["TOTALLY_MADE_UP_TYPE"]
    assert at.is_light(unknown) is False
    assert at.is_switch(unknown) is False
    assert at.is_cover(unknown) is False
    assert at.is_climate(unknown) is False
    assert at.is_button(unknown) is False
    assert at.is_lock(unknown) is False


def test_matches_when_one_of_several_types_matches(at):
    """A device reporting multiple types matches if any one type is known."""
    assert at.is_climate(["SOMETHING_ELSE", "AIR_CONDITION"]) is True


def test_empty_type_list_matches_nothing(at):
    assert at.is_switch([]) is False
    assert at.is_climate([]) is False
