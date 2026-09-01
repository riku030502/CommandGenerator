"""Smoke tests for the GPSR web interface.

Run with:  ./run_tests.sh

These drive the real NiceGUI page through the framework's user simulation, so a
pass means the buttons actually work against the data in ``data/`` - not just
that the module imports.
"""

import sys

from nicegui.testing import User


def _ui_module():
    return sys.modules["robocupathome_generator.ui.gpsr_ui"]


async def test_page_loads(user: User) -> None:
    await user.open("/")
    await user.should_see("Generate GPSR Commands")


async def test_generate_three_commands(user: User) -> None:
    await user.open("/")
    user.find("Generate GPSR Commands").click()
    await user.should_see("New Command")

    commands = _ui_module().gpsrui.commands
    assert len(commands) == 3, f"expected 3 commands, got {len(commands)}"
    assert all(c.command.strip() for c in commands), "an empty command was generated"
    assert {c.kind for c in commands} == {"people", "objects", ""}

    print("\ngenerated commands:")
    for c in commands:
        print(f"  ({c.kind or 'any'}) {c.command}")


async def test_lock_and_show_switches_to_task_view(user: User) -> None:
    await user.open("/")
    user.find("Generate GPSR Commands").click()
    await user.should_see("New Command")
    user.find("Lock & Show").click()
    await user.should_see("Text size")
