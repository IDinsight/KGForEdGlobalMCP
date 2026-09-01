"""This module contains framework-independent regular expressions used across the
backend.
"""

# Standard Library
import re

from typing import Final

# Matches an allowlisted manifest artifact name.
ARTIFACT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")

# Matches ASCII control characters that are unsafe in identifiers and paths.
CONTROL_CHARACTER_RE = re.compile(r"[\x00-\x1f\x7f]")

# Delivery artifacts carry standards and learning components together, so their names
# take the ``as_lc_`` prefix. These patterns gate package construction only; already
# built packages resolve their artifacts through the paths recorded in their manifest.
DELIVERY_NODES_BASENAME_RE: Final[re.Pattern[str]] = re.compile(
    r"^as_lc_nodes_[A-Za-z0-9][A-Za-z0-9_-]*\.jsonl$"
)
DELIVERY_RELATIONSHIPS_BASENAME_RE: Final[re.Pattern[str]] = re.compile(
    r"^as_lc_relationships_[A-Za-z0-9][A-Za-z0-9_-]*\.jsonl$"
)

# Matches graph package IDs based on a snapshot, with an optional future package suffix.
GRAPH_PACKAGE_ID_RE = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*@"
    r"[a-z0-9]+(?:[._-][a-z0-9]+)*\+"
    r"[0-9a-f]{12}"
    r"(?:--[a-z0-9]+(?:-[a-z0-9]+)*--p[1-9][0-9]*)?$"
)

# Matches lowercase kebab-case registry keys such as framework and profile IDs.
KEBAB_CASE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Matches a conservative BCP 47-shaped language tag.
LANGUAGE_TAG_RE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")

# Matches a fully qualified lowercase SHA-256 checksum.
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

SAFE_AS_ARTIFACT_BASENAME_RE: Final[re.Pattern[str]] = re.compile(
    r"^as_[A-Za-z0-9][A-Za-z0-9._-]*\.(?:json|jsonl)$"
)

# Matches snapshot IDs in the form <framework>@<version>+<12-character-hash>.
SNAPSHOT_ID_RE = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*@[a-z0-9]+(?:[._-][a-z0-9]+)*\+[0-9a-f]{12}$"
)

# Matches a standard JSON Web Token (JWT) or similar 3-part base64url-encoded string.
# (?i) makes it case-insensitive. It optionally matches the word "bearer " before the
# token. The core pattern matches exactly three chunks of
# letters/numbers/hyphens/underscores separated by dots.
TOKEN_RE = re.compile(
    r"(?i)\b(?:bearer\s+)?([A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+)"
)

# Matches version tokens that are safe as registry and filesystem segments.
VERSION_TOKEN_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
