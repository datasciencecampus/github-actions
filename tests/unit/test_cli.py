import json

import pytest

from precommit_updates import cli
from precommit_updates.github import GitHubQueryError


def test_write_output_preserves_workflow_keys_and_json(tmp_path, monkeypatch):
    output = tmp_path / "github-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))

    cli._write_output({"updates_found": "true", "updates_json": [{"repo": "example"}]})

    assert output.read_text().splitlines() == [
        "updates_found=true",
        'updates_json=[{"repo":"example"}]',
    ]


def test_detect_command_reports_indeterminate_github_query(tmp_path, monkeypatch, capsys):
    config = tmp_path / "pre-commit-config.yaml"
    tracking = tmp_path / "tracking.json"
    summary = tmp_path / "summary.md"
    config.write_text("repos: []\n")
    tracking.write_text('{"hooks": {}}')
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    def fail_detection(config_path, tracking_path, github):
        raise GitHubQueryError("rate limit exceeded")

    monkeypatch.setattr(cli, "detect_updates", fail_detection)

    try:
        cli.detect_command(type("Args", (), {"config": str(config), "tracking": str(tracking)})())
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("expected detection to fail")

    assert "Detection indeterminate" in summary.read_text()
    assert "rate limit exceeded" in capsys.readouterr().out


def test_detect_command_skips_detection_when_auto_updates_are_disabled(tmp_path, monkeypatch, capsys):
    config = tmp_path / "pre-commit-config.yaml"
    tracking = tmp_path / "tracking.json"
    settings = tmp_path / "settings.json"
    output = tmp_path / "github-output"
    summary = tmp_path / "summary.md"
    config.write_text("repos: []\n")
    tracking.write_text('{"hooks": {}}')
    settings.write_text('{"enable_auto_updates": false}')
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    def fail_detection(config_path, tracking_path, github):
        raise AssertionError("detection should be skipped")

    monkeypatch.setattr(cli, "detect_updates", fail_detection)

    cli.detect_command(
        type("Args", (), {"config": str(config), "tracking": str(tracking), "settings": str(settings)})()
    )

    values = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert values["auto_updates_enabled"] == "false"
    assert values["updates_found"] == "false"
    assert json.loads(values["updates_json"]) == []
    assert "detection and tracking-state mutation" in summary.read_text()
    assert "Auto updates disabled" in capsys.readouterr().out


def test_detect_command_reports_when_no_comparable_updates_are_found(tmp_path, monkeypatch, capsys):
    config = tmp_path / "pre-commit-config.yaml"
    tracking = tmp_path / "tracking.json"
    summary = tmp_path / "summary.md"
    config.write_text("repos: []\n")
    tracking.write_text('{"hooks": {}}')
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setattr(cli, "detect_updates", lambda config_path, tracking_path, github: [])

    cli.detect_command(type("Args", (), {"config": str(config), "tracking": str(tracking)})())

    assert "No comparable updates detected" in summary.read_text()
    assert "unsupported host or tag format" in summary.read_text()
    assert "No comparable pre-commit updates" in capsys.readouterr().out


def test_write_summary_appends_markdown(tmp_path, monkeypatch):
    summary = tmp_path / "summary"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    cli._write_summary("## Status\n\nAll clear")

    assert summary.read_text() == "## Status\n\nAll clear\n"


def test_cooldown_command_reads_settings_file_defaults(tmp_path, monkeypatch):
    tracking = tmp_path / "tracking.json"
    settings = tmp_path / "settings.json"
    tracking.write_text(json.dumps({"hooks": {}}))
    settings.write_text(json.dumps({"cooldown_days": {"major": 28, "minor": 14, "patch": 21}}))
    output = tmp_path / "github-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv(
        "UPDATES_JSON",
        json.dumps(
            [
                {
                    "repo": "example",
                    "semver_level": "patch",
                    "candidate_first_seen_at": "2999-09-01T00:00:00+00:00",
                }
            ]
        ),
    )

    cli.cooldown_command(type("Args", (), {"tracking": str(tracking), "settings": str(settings)})())

    values = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert json.loads(values["eligible_updates"]) == []
    assert json.loads(values["skipped_updates"])[0]["reason"].endswith("/21 days")


def test_cooldown_command_environment_overrides_settings_file(tmp_path, monkeypatch):
    tracking = tmp_path / "tracking.json"
    settings = tmp_path / "settings.json"
    tracking.write_text(json.dumps({"hooks": {}}))
    settings.write_text(json.dumps({"cooldown_days": {"patch": 21}}))
    output = tmp_path / "github-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("COOLDOWN_PATCH", "7")
    monkeypatch.setenv(
        "UPDATES_JSON",
        json.dumps(
            [
                {
                    "repo": "example",
                    "semver_level": "patch",
                    "candidate_first_seen_at": "2026-09-01T00:00:00+00:00",
                }
            ]
        ),
    )

    cli.cooldown_command(type("Args", (), {"tracking": str(tracking), "settings": str(settings)})())

    values = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert json.loads(values["eligible_updates"])[0]["repo"] == "example"
    assert json.loads(values["skipped_updates"]) == []


@pytest.mark.parametrize("invalid_value", [0.9, True])
def test_effective_cooldown_rejects_non_integer_settings(invalid_value):
    settings = {"cooldown_days": {"major": 28, "minor": 14, "patch": invalid_value}}

    with pytest.raises(ValueError, match="cooldown periods must be integers"):
        cli._effective_cooldown(settings)


def test_cooldown_command_reads_persistent_skip_list(tmp_path, monkeypatch):
    tracking = tmp_path / "tracking.json"
    settings = tmp_path / "settings.json"
    tracking.write_text(json.dumps({"hooks": {}}))
    settings.write_text(json.dumps({"hooks_to_skip": ["example"]}))
    output = tmp_path / "github-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv(
        "UPDATES_JSON",
        json.dumps([{"repo": "example", "semver_level": "patch", "candidate_first_seen_at": "2026-09-01T00:00:00+00:00"}]),
    )

    cli.cooldown_command(type("Args", (), {"tracking": str(tracking), "settings": str(settings)})())

    values = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert json.loads(values["eligible_updates"]) == []
    assert json.loads(values["skipped_updates"])[0]["reason"] == "Hook in skip list"


def test_cooldown_command_environment_skip_list_overrides_settings_file(tmp_path, monkeypatch):
    tracking = tmp_path / "tracking.json"
    settings = tmp_path / "settings.json"
    tracking.write_text(json.dumps({"hooks": {}}))
    settings.write_text(json.dumps({"hooks_to_skip": ["example"]}))
    output = tmp_path / "github-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("SKIP_HOOKS", "other")
    monkeypatch.setenv(
        "UPDATES_JSON",
        json.dumps([{"repo": "example", "semver_level": "patch", "candidate_first_seen_at": "2026-09-01T00:00:00+00:00"}]),
    )

    cli.cooldown_command(type("Args", (), {"tracking": str(tracking), "settings": str(settings)})())

    values = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert json.loads(values["eligible_updates"])[0]["repo"] == "example"
    assert json.loads(values["skipped_updates"]) == []


def test_cooldown_command_honors_disabled_settings_file(tmp_path, monkeypatch):
    tracking = tmp_path / "tracking.json"
    settings = tmp_path / "settings.json"
    tracking.write_text(json.dumps({"hooks": {}}))
    settings.write_text(json.dumps({"enable_auto_updates": False}))
    output = tmp_path / "github-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv(
        "UPDATES_JSON",
        json.dumps([{"repo": "example", "semver_level": "patch", "candidate_first_seen_at": "2026-09-01T00:00:00+00:00"}]),
    )

    cli.cooldown_command(type("Args", (), {"tracking": str(tracking), "settings": str(settings)})())

    values = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert json.loads(values["eligible_updates"]) == []
    assert json.loads(values["skipped_updates"])[0]["reason"] == "Auto updates disabled in configuration"


def test_update_branch_name_is_unique_per_workflow_attempt(monkeypatch):
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")

    assert cli._update_branch_name() == "chore/precommit-updates-12345-2"


def test_validate_command_accepts_aligned_files(tmp_path, capsys):
    config = tmp_path / "pre-commit-config.yaml"
    tracking = tmp_path / "tracking.json"
    repo = "https://github.com/example/hooks"
    sha = "a" * 40
    config.write_text(f"repos:\n  - repo: {repo}\n    rev: {sha}\n")
    tracking.write_text(json.dumps({"hooks": {repo: {"current_sha": sha}}}))

    cli.validate_command(type("Args", (), {"config": str(config), "tracking": str(tracking)})())

    assert "aligned" in capsys.readouterr().out


def test_validate_command_rejects_sha_mismatch(tmp_path, capsys):
    config = tmp_path / "pre-commit-config.yaml"
    tracking = tmp_path / "tracking.json"
    repo = "https://github.com/example/hooks"
    config.write_text(f"repos:\n  - repo: {repo}\n    rev: {'a' * 40}\n")
    tracking.write_text(json.dumps({"hooks": {repo: {"current_sha": "b" * 40}}}))

    try:
        cli.validate_command(type("Args", (), {"config": str(config), "tracking": str(tracking)})())
    except SystemExit as error:
        assert error.code == 1
    else:
        raise AssertionError("expected validation to fail")

    assert "SHA mismatch" in capsys.readouterr().out


def test_validate_command_initializes_missing_tracking_file(tmp_path, capsys):
    config = tmp_path / "pre-commit-config.yaml"
    tracking = tmp_path / "tracking.json"
    repo = "https://github.com/example/hooks"
    sha = "a" * 40
    config.write_text(f"repos:\n  - repo: {repo}\n    rev: {sha}\n")

    cli.validate_command(type("Args", (), {"config": str(config), "tracking": str(tracking)})())

    state = json.loads(tracking.read_text())
    assert state["hooks"][repo]["current_sha"] == sha
    assert "not found; creating baseline" in capsys.readouterr().out