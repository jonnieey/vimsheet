"""E2E tests for sheet commands (quoted names, copy/dup semantics)."""

from __future__ import annotations

import pytest

from tests.conftest import make_workbook
from vimsheet.app import VimSheetApp


@pytest.fixture
def app() -> VimSheetApp:
    return VimSheetApp(workbook=make_workbook())


@pytest.mark.asyncio
async def test_sheet_rename_with_spaces(app: VimSheetApp) -> None:
    async with app.run_test():
        app._dispatch_command('sheet rename "Q1 Sales"')
        assert app.workbook.active_sheet.name == "Q1 Sales"


@pytest.mark.asyncio
async def test_sheet_add_with_spaces(app: VimSheetApp) -> None:
    async with app.run_test():
        app._dispatch_command('sa "Q1 Sales"')
        assert app.workbook.sheets[-1].name == "Q1 Sales"


@pytest.mark.asyncio
async def test_sheet_delete_with_spaces(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        app._dispatch_command('sa "Q1 Sales"')
        await pilot.pause()
        assert any(s.name == "Q1 Sales" for s in app.workbook.sheets)
        app._dispatch_command('sd "Q1 Sales"')
        await pilot.pause()
        assert not any(s.name == "Q1 Sales" for s in app.workbook.sheets)


@pytest.mark.asyncio
async def test_sc_one_arg_renames_active(app: VimSheetApp) -> None:
    async with app.run_test():
        app._dispatch_command('sc "New Name"')
        assert app.workbook.active_sheet.name == "New Name"


@pytest.mark.asyncio
async def test_sc_two_args_duplicates(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        app._dispatch_command('sa "Src"')
        await pilot.pause()
        app._dispatch_command('sc "Src" "Copy Name"')
        await pilot.pause()
        names = [s.name for s in app.workbook.sheets]
        assert "Src" in names
        assert "Copy Name" in names


@pytest.mark.asyncio
async def test_sheet_copy_two_args_duplicates(app: VimSheetApp) -> None:
    async with app.run_test() as pilot:
        app._dispatch_command('sa "Src"')
        await pilot.pause()
        app._dispatch_command('sheet copy "Src" "Copy Name"')
        await pilot.pause()
        names = [s.name for s in app.workbook.sheets]
        assert "Copy Name" in names


@pytest.mark.asyncio
async def test_sdup_no_args_duplicates_active_with_suffix(app: VimSheetApp) -> None:
    async with app.run_test():
        orig = app.workbook.active_sheet.name
        app._dispatch_command("sdup")
        names = [s.name for s in app.workbook.sheets]
        assert f"{orig} (copy)" in names
