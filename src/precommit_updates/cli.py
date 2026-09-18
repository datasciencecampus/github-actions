"""Command-line entrypoints for workflow stages."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from .detection import detect_updates
from .github import GitHubClient, GitHubQueryError
from .models import CooldownConfig
from .mutation import apply_updates
from .policy import filter_updates
from .pr_body import extract_hook_name, generate_pr_body
from .release_info import enrich_updates
from .validation import alignment_errors, initialize_tracking


DEFAULT_UPDATE_SETTINGS: dict[str, Any] = {
    "cooldown_days": {"major": 28, "minor": 14, "patch": 7},
    "hooks_to_skip": [],
    "enable_auto_updates": True,
}


def _write_output(values: dict[str, Any]) -> None:
    """Write step outputs to ``GITHUB_OUTPUT`` or standard output.

    Args:
        values: Output names and values to serialize as one-line JSON records.
    """
    output_path = os.environ.get("GITHUB_OUTPUT")
    for key, value in values.items():
        serialized = json.dumps(value, separators=(",", ":")) if not isinstance(value, str) else value
        if output_path:
            with open(output_path, "a") as output_file:
                output_file.write(f"{key}={serialized}\n")
        else:
            print(f"{key}={serialized}")


def _write_summary(markdown: str) -> None:
    """Append Markdown to the GitHub Actions step summary when available."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        try:
            with open(summary_path, "a") as summary_file:
                summary_file.write(f"{markdown.rstrip()}\n")
        except OSError as error:
            print(f"WARNING: Could not write GitHub step summary: {error}")


def _write_notice(title: str, message: str) -> None:
    """Emit a readable GitHub Actions notice, or a local equivalent."""
    print(f"::notice title={title}::{message}")


def _path(value: str) -> Path:
    """Expand a command-line path value.

    Args:
        value: User-provided filesystem path.

    Returns:
        Expanded path object.
    """
    return Path(value).expanduser()


def _load_update_settings(path: Path) -> dict[str, Any]:
    """Load persistent update settings with secure built-in defaults."""
    settings = {
        "cooldown_days": dict(DEFAULT_UPDATE_SETTINGS["cooldown_days"]),
        "hooks_to_skip": list(DEFAULT_UPDATE_SETTINGS["hooks_to_skip"]),
        "enable_auto_updates": DEFAULT_UPDATE_SETTINGS["enable_auto_updates"],
    }
    if not path.exists():
        return settings

    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise ValueError("update settings must be a JSON object")

    cooldown_days = loaded.get("cooldown_days")
    if cooldown_days is not None:
        if not isinstance(cooldown_days, dict):
            raise ValueError("cooldown_days must be a JSON object")
        settings["cooldown_days"].update(cooldown_days)

    hooks_to_skip = loaded.get("hooks_to_skip")
    if hooks_to_skip is not None:
        if not isinstance(hooks_to_skip, list) or not all(isinstance(item, str) for item in hooks_to_skip):
            raise ValueError("hooks_to_skip must be a list of strings")
        settings["hooks_to_skip"] = hooks_to_skip

    enable_auto_updates = loaded.get("enable_auto_updates")
    if enable_auto_updates is not None:
        if not isinstance(enable_auto_updates, bool):
            raise ValueError("enable_auto_updates must be a boolean")
        settings["enable_auto_updates"] = enable_auto_updates

    return settings


def _env_int(name: str, fallback: int) -> int:
    """Return an integer environment override or a fallback value."""
    value = os.environ.get(name)
    return int(value) if value not in (None, "") else fallback


def _effective_cooldown(settings: dict[str, Any]) -> CooldownConfig:
    """Combine persistent cooldown settings with explicit workflow overrides."""
    configured = settings["cooldown_days"]
    return CooldownConfig(
        major=_env_int("COOLDOWN_MAJOR", configured["major"]),
        minor=_env_int("COOLDOWN_MINOR", configured["minor"]),
        patch=_env_int("COOLDOWN_PATCH", configured["patch"]),
    )


def _effective_skip_hooks(settings: dict[str, Any]) -> list[str]:
    """Combine persistent skip hooks with explicit workflow overrides."""
    override = os.environ.get("SKIP_HOOKS")
    if override not in (None, ""):
        return [item.strip() for item in override.split(",") if item.strip()]
    return [item.strip() for item in settings["hooks_to_skip"] if item.strip()]


def detect_command(args: argparse.Namespace) -> None:
    """Run the update-detection workflow stage.

    Args:
        args: Parsed CLI arguments containing config, tracking, and settings paths.
    """
    settings = _load_update_settings(_path(getattr(args, "settings", "configs/precommit-updates-config.json")))
    if not settings["enable_auto_updates"]:
        _write_output({"auto_updates_enabled": "false", "updates_found": "false", "updates_json": []})
        _write_notice("Auto updates disabled", "configs/precommit-updates-config.json disables auto updates.")
        _write_summary(
            "## Pre-commit update check\n\n"
            "> **Auto updates disabled**\n\n"
            "The workflow skipped update detection and tracking-state mutation."
        )
        return

    _write_output({"auto_updates_enabled": "true"})
    try:
        updates = detect_updates(_path(args.config), _path(args.tracking), GitHubClient())
    except GitHubQueryError as error:
        print(f"ERROR: Pre-commit update detection is indeterminate: {error}")
        _write_summary(
            "## Pre-commit update check\n\n"
            "> **Detection indeterminate**\n\n"
            f"{error}\n\n"
            "The workflow could not reliably query GitHub release data, so it did not treat hooks as current."
        )
        raise SystemExit(1) from error
    _write_output({"updates_found": "true" if updates else "false", "updates_json": updates})
    if not updates:
        _write_notice("No comparable pre-commit updates", "No comparable updates were detected.")
        _write_summary(
            "## Pre-commit update check\n\n"
            "> **No comparable updates detected**\n\n"
            "No comparable updates were detected. Hooks may already be current, use an unsupported "
            "host or tag format, or have a current SHA that could not be resolved to a comparable SemVer tag."
        )
        return

    rows = [
        f"| `{update['repo']}` | `{update['old_version']}` | `{update['new_version']}` |"
        for update in updates
    ]
    _write_summary(
        "## Pre-commit update check\n\n"
        f"> **{len(updates)} update(s) available**\n\n"
        "| Hook | Current | Latest |\n| --- | --- | --- |\n"
        + "\n".join(rows)
    )


def cooldown_command(args: argparse.Namespace) -> None:
    """Run the cooldown-policy workflow stage.

    Args:
        args: Parsed CLI arguments containing the tracking path.
    """
    updates = json.loads(os.environ.get("UPDATES_JSON", "[]"))
    tracking_path = _path(args.tracking)
    tracking = json.loads(tracking_path.read_text()) if tracking_path.exists() else {"hooks": {}}
    settings = _load_update_settings(_path(args.settings))
    if not settings["enable_auto_updates"]:
        skipped = [{**update, "reason": "Auto updates disabled in configuration"} for update in updates]
        _write_output({"eligible_updates": [], "skipped_updates": skipped})
        _write_notice("Auto updates disabled", "configs/precommit-updates-config.json disables auto updates.")
        _write_summary(
            "## Cooldown filter\n\n"
            f"| Result | Count |\n| --- | ---: |\n| Eligible | 0 |\n| Skipped | {len(skipped)} |\n\n"
            "> **Auto updates disabled**\n\n"
            "The workflow stopped before release enrichment and pull request creation."
        )
        return

    cooldown = _effective_cooldown(settings)
    skip_hooks = _effective_skip_hooks(settings)
    eligible, skipped = filter_updates(
        updates,
        tracking,
        cooldown,
        now=datetime.now(timezone.utc),
        force_update=os.environ.get("FORCE_UPDATE", "false").lower() == "true",
        skip_hooks=skip_hooks,
    )
    _write_output({"eligible_updates": eligible, "skipped_updates": skipped})
    if not eligible:
        _write_notice(
            "No updates after cooldown",
            f"{len(skipped)} available update(s) were skipped; downstream jobs will not run.",
        )
    _write_summary(
        "## Cooldown filter\n\n"
        f"| Result | Count |\n| --- | ---: |\n| Eligible | {len(eligible)} |\n"
        f"| Skipped | {len(skipped)} |\n\n"
        + (
            "> **No eligible updates**\n\n"
            "The workflow stopped before release enrichment and pull request creation."
            if not eligible
            else "> Eligible updates will continue to release enrichment."
        )
    )


def release_info_command(args: argparse.Namespace) -> None:
    """Run the release-enrichment workflow stage.

    Args:
        args: Parsed CLI arguments; update data is read from ``ELIGIBLE_JSON``.
    """
    updates = json.loads(os.environ.get("ELIGIBLE_JSON", "[]"))
    _write_output({"release_info": enrich_updates(updates, GitHubClient())})


def apply_command(args: argparse.Namespace) -> None:
    """Apply updates, commit them, push a branch, and create a pull request.

    Args:
        args: Parsed CLI arguments containing config and tracking paths.

    Raises:
        SystemExit: If a git or GitHub CLI command fails.
    """
    release_info = json.loads(os.environ.get("RELEASE_INFO", "[]"))
    skipped = json.loads(os.environ.get("SKIPPED_UPDATES", "[]"))
    if not release_info:
        print("No updates to apply")
        return

    cooldown = _effective_cooldown(_load_update_settings(_path(args.settings))).as_dict()
    body = generate_pr_body(
        release_info,
        skipped,
        cooldown,
        force_update=os.environ.get("FORCE_UPDATE", "false").lower() == "true",
        actor=os.environ.get("GITHUB_ACTOR", "Workflow"),
        run_id=os.environ.get("GITHUB_RUN_ID", "local"),
        repository=os.environ.get("GITHUB_REPOSITORY", "unknown"),
        server_url=os.environ.get("GITHUB_SERVER_URL", "https://github.com"),
    )
    branch = f"chore/precommit-updates-{datetime.now(timezone.utc):%Y%m%d}"
    setup_commands = [
        ["git", "config", "user.name", "github-actions[bot]"],
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        ["git", "checkout", "-b", branch],
    ]

    for command in setup_commands:
        result = subprocess.run(command, text=True, capture_output=True)
        if result.returncode != 0:
            raise SystemExit(result.stderr or f"Command failed: {' '.join(command[:3])}")

    for update in release_info:
        apply_updates(_path(args.config), _path(args.tracking), [update])
        hook_name = extract_hook_name(update["repo"])
        commands = [
            ["git", "add", str(args.config), str(args.tracking)],
            [
                "git",
                "commit",
                "-m",
                f"chore(pre-commit): update {hook_name} to {update['new_version']}",
            ],
        ]
        for command in commands:
            result = subprocess.run(command, text=True, capture_output=True)
            if result.returncode != 0:
                raise SystemExit(result.stderr or f"Command failed: {' '.join(command[:3])}")

    final_commands = [
        ["gh", "auth", "setup-git"],
        ["git", "push", "--force-with-lease", "-u", "origin", branch],
        [
            "gh",
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            branch,
            "--title",
            f"chore(pre-commit): auto-update hooks ({len(release_info)} update(s))",
            "--body",
            body,
        ],
    ]
    for command in final_commands:
        result = subprocess.run(command, text=True, capture_output=True)
        if result.returncode != 0:
            raise SystemExit(result.stderr or f"Command failed: {' '.join(command[:3])}")


def validate_command(args: argparse.Namespace) -> None:
    """Validate pre-commit configuration and tracking alignment."""
    tracking_path = _path(args.tracking)
    if not tracking_path.exists():
        print(f"WARNING: {tracking_path} not found; creating baseline tracking state")
        initialize_tracking(_path(args.config), tracking_path)
        return

    errors = alignment_errors(_path(args.config), tracking_path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("Pre-commit configuration and tracking state are aligned")


def _parser() -> argparse.ArgumentParser:
    """Build the command-line parser for all workflow stages.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(prog="precommit-updates")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("detect", "cooldown", "release-info", "apply", "validate"):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--config", default=".pre-commit-config.yaml")
        subparser.add_argument("--tracking", default="configs/precommit-update-tracking.json")
        subparser.add_argument("--settings", default="configs/precommit-updates-config.json")
        subparser.set_defaults(handler=globals()[f"{name.replace('-', '_')}_command"])
    return parser


def main() -> None:
    """Parse arguments and dispatch the selected workflow stage."""
    args = _parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()