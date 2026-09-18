"""Domain values and pure version logic for pre-commit updates."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional


Version = tuple[int, int, int]
SEMVER_LEVELS = ("major", "minor", "patch")
_VERSION_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")
_SHA_PATTERN = re.compile(r"^[0-9a-f]{7,40}$", re.IGNORECASE)


@dataclass(frozen=True)
class CooldownConfig:
    """Validated cooldown durations, in whole days.

    Attributes:
        major: Minimum days before a major update is eligible.
        minor: Minimum days before a minor update is eligible.
        patch: Minimum days before a patch update is eligible.
    """

    major: int = 28
    minor: int = 14
    patch: int = 7

    def __post_init__(self) -> None:
        """Validate that cooldown values are non-negative integers.

        Raises:
            ValueError: If any cooldown is not an integer or is negative.
        """
        values = {"major": self.major, "minor": self.minor, "patch": self.patch}
        if any(not isinstance(value, int) or isinstance(value, bool) for value in values.values()):
            raise ValueError("cooldown periods must be integers")
        if any(value < 0 for value in values.values()):
            raise ValueError("cooldown periods cannot be negative")

    def for_level(self, level: str) -> int:
        """Return the configured duration for a semantic version level.

        Args:
            level: One of ``major``, ``minor``, or ``patch``.

        Returns:
            The cooldown duration in days.

        Raises:
            ValueError: If ``level`` is unsupported.
        """
        if level not in SEMVER_LEVELS:
            raise ValueError(f"unsupported semver level: {level}")
        return getattr(self, level)

    def as_dict(self) -> dict[str, int]:
        """Return cooldown values keyed by semantic version level.

        Returns:
            A new dictionary containing the major, minor, and patch durations.
        """
        return {level: self.for_level(level) for level in SEMVER_LEVELS}


def parse_version(tag: str) -> Optional[Version]:
    """Parse a semantic version tag such as ``v1.2.3``.

    Args:
        tag: Version tag with an optional ``v`` prefix and prerelease/build suffix.

    Returns:
        A ``(major, minor, patch)`` tuple, or ``None`` for an invalid tag.
    """
    match = _VERSION_PATTERN.fullmatch(tag.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def determine_semver_level(old_version: str, new_version: str) -> str:
    """Classify a version change.

    Args:
        old_version: Existing semantic version tag.
        new_version: Candidate semantic version tag.

    Returns:
        ``major``, ``minor``, ``patch``, or ``unknown`` when either version is invalid or not an upgrade.
    """
    old = parse_version(old_version)
    new = parse_version(new_version)
    if not old or not new:
        return "unknown"
    if new <= old:
        return "unknown"
    if old[0] != new[0]:
        return "major"
    if old[1] != new[1]:
        return "minor"
    return "patch"


def is_sha_like_version(version: str) -> bool:
    """Return whether a version value looks like a commit SHA.

    Args:
        version: Version or commit identifier to inspect.

    Returns:
        ``True`` when the value contains 7 to 40 hexadecimal characters.
    """
    return bool(_SHA_PATTERN.fullmatch(version.strip()))