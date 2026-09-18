import pytest

from precommit_updates.models import (
    CooldownConfig,
    determine_semver_level,
    is_sha_like_version,
    parse_version,
)


@pytest.mark.parametrize(
    ("tag", "expected"),
    [("v1.2.3", (1, 2, 3)), ("1.2.3", (1, 2, 3)), ("v1.2.3-rc.1", (1, 2, 3)), ("1.2", None)],
)
def test_parse_version(tag, expected):
    assert parse_version(tag) == expected


@pytest.mark.parametrize(
    ("old", "new", "level"),
    [
        ("v1.2.3", "v2.0.0", "major"),
        ("v1.2.3", "v1.3.0", "minor"),
        ("v1.2.3", "v1.2.4", "patch"),
        ("sha", "v1.2.4", "unknown"),
        ("v2.0.0", "v1.9.9", "unknown"),
        ("v1.3.0", "v1.2.9", "unknown"),
        ("v1.2.4", "v1.2.3", "unknown"),
        ("v1.2.3", "1.2.3", "unknown"),
    ],
)
def test_determine_semver_level(old, new, level):
    assert determine_semver_level(old, new) == level


def test_sha_detection_is_generic():
    assert is_sha_like_version("a" * 40)
    assert not is_sha_like_version("v1.2.3")


def test_cooldown_config_rejects_negative_values():
    with pytest.raises(ValueError, match="negative"):
        CooldownConfig(patch=-1)