"""Tests for GAIA OS CLI commands and single-shot execution."""

import pytest
from click.testing import CliRunner

from gaia.cli.cli import main


@pytest.fixture
def cli_runner(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory) -> CliRunner:
    db_file = tmp_path / "test_cli.db"
    monkeypatch.setenv("GAIA_DATABASE_PATH", str(db_file))
    monkeypatch.setenv("GAIA_PROVIDER_TYPE", "rule_based")
    return CliRunner()


def test_cli_project_create_and_list(cli_runner: CliRunner) -> None:
    # 1. Create project
    res_create = cli_runner.invoke(
        main, ["project", "create", "Project Titan", "-d", "Heavy infrastructure"]
    )
    assert res_create.exit_code == 0
    assert "Project created: Project Titan" in res_create.output

    # 2. List projects
    res_list = cli_runner.invoke(main, ["project", "list"])
    assert res_list.exit_code == 0
    assert "Project Titan" in res_list.output


def test_cli_context_show_and_set(cli_runner: CliRunner) -> None:
    res_show = cli_runner.invoke(main, ["context", "show"])
    assert res_show.exit_code == 0
    assert "Current Project ID" in res_show.output


def test_cli_single_shot_natural_language_query(cli_runner: CliRunner) -> None:
    # Single-shot create note
    res = cli_runner.invoke(main, ["create note CLI Test Note with content Tested via CLI runner"])
    assert res.exit_code == 0
    assert "CLI Test Note" in res.output
    assert "create_note" in res.output
