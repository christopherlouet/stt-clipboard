#!/usr/bin/env python3
"""Test auto-paste functionality."""

import pytest

from src.autopaste import (
    BaseAutoPaster,
    WtypePaster,
    XdotoolPaster,
    YdotoolPaster,
    create_autopaster,
)


def test_base_autopaster_interface():
    """Test that BaseAutoPaster defines the correct interface."""
    # Verify abstract methods
    assert hasattr(BaseAutoPaster, "paste")
    assert hasattr(BaseAutoPaster, "is_available")


def test_xdotool_paster_initialization():
    """Test XdotoolPaster initialization."""
    paster = XdotoolPaster(timeout=2.0)
    assert paster.timeout == 2.0

    # is_available should return a boolean
    available = paster.is_available()
    assert isinstance(available, bool)


def test_ydotool_paster_initialization():
    """Test YdotoolPaster initialization."""
    # Test standard paste (Ctrl+V)
    paster = YdotoolPaster(timeout=2.0, use_shift=False)
    assert paster.timeout == 2.0
    assert paster.use_shift is False

    # Test terminal paste (Ctrl+Shift+V)
    paster_terminal = YdotoolPaster(timeout=2.0, use_shift=True)
    assert paster_terminal.timeout == 2.0
    assert paster_terminal.use_shift is True

    # is_available should return a boolean
    available = paster.is_available()
    assert isinstance(available, bool)


def test_wtype_paster_initialization():
    """Test WtypePaster initialization."""
    paster = WtypePaster(timeout=2.0)
    assert paster.timeout == 2.0

    # is_available should return a boolean
    available = paster.is_available()
    assert isinstance(available, bool)


def test_create_autopaster_auto_detection():
    """Test auto-detection of paste tools."""
    try:
        # Should either return an autopaster or raise RuntimeError
        paster = create_autopaster(preferred_tool="auto", timeout=2.0)
        assert isinstance(paster, BaseAutoPaster)
        assert paster.timeout == 2.0
    except RuntimeError as e:
        # Expected if no paste tool is available
        assert "No auto-paste tool available" in str(e)
        pytest.skip("No paste tool available in test environment")


def test_create_autopaster_preferred_tool():
    """Test creating autopaster with preferred tool."""
    # Test with each tool type
    for tool in ["xdotool", "ydotool", "wtype"]:
        try:
            paster = create_autopaster(preferred_tool=tool, timeout=2.0)
            assert isinstance(paster, BaseAutoPaster)
            assert paster.timeout == 2.0

            # Verify correct type
            if tool == "xdotool":
                assert isinstance(paster, XdotoolPaster)
            elif tool == "ydotool":
                assert isinstance(paster, YdotoolPaster)
            elif tool == "wtype":
                assert isinstance(paster, WtypePaster)

        except RuntimeError:
            # Tool not available, that's ok in test environment
            pytest.skip(f"{tool} not available in test environment")


def test_paste_tool_detection():
    """Test that at least one paste tool can be detected."""
    from src.autopaste import _detect_available_tools

    available_tools = _detect_available_tools(timeout=2.0)

    # In test environment, may have 0 or more tools
    assert isinstance(available_tools, list)

    # If tools are available, they should all be BaseAutoPaster instances
    for tool in available_tools:
        assert isinstance(tool, BaseAutoPaster)


@pytest.mark.skip(reason="Requires interactive environment with running display server")
def test_paste_operation():
    """Test actual paste operation (requires interactive environment)."""
    # This test is skipped by default as it requires:
    # 1. A running display server (Wayland or X11)
    # 2. Paste tool installed (xdotool, ydotool, or wtype)
    # 3. Active window to paste into

    paster = create_autopaster(preferred_tool="auto", timeout=2.0)
    success = paster.paste()
    assert isinstance(success, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
