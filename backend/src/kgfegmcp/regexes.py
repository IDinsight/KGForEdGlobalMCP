"""This module contains regexes used across the codebase. They are defined here to
avoid duplication and to ensure consistency.
"""

# Standard Library
import re

# Matches a standard JSON Web Token (JWT) or similar 3-part base64url-encoded string.
# (?i) makes it case-insensitive. It optionally matches the word "bearer " before the
# token. The core pattern matches exactly three chunks of
# letters/numbers/hyphens/underscores separated by dots.
TOKEN_RE = re.compile(
    r"(?i)\b(?:bearer\s+)?([A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+)"
)
