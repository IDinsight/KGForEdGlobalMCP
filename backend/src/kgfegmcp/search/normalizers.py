"""Provide versioned deterministic normalization for lexical, facet, and code search."""

# Future Library
from __future__ import annotations

# Standard Library
import unicodedata

from dataclasses import dataclass
from typing import Final

# Package Library
from kgfegmcp.errors import CatalogError
from kgfegmcp.profiles.models import CodeSearchPolicy

CODE_NORMALIZER_VERSION: Final[str] = "profile_code_nfkc_v1"
FACET_NORMALIZER_VERSION: Final[str] = "facet_nfkc_casefold_whitespace_v1"
LEXICAL_NORMALIZER_VERSION: Final[str] = "lexical_nfkc_casefold_tokens_v1"


@dataclass(frozen=True, slots=True)
class CodeNormalizer:
    """Normalize statement codes only according to one exact profile policy."""

    case_sensitive: bool
    normalized_delimiters: tuple[str, ...]
    punctuation_normalization: bool
    source_delimiters: tuple[str, ...]
    whitespace_normalization: bool

    @classmethod
    def from_policy(cls, policy: CodeSearchPolicy) -> CodeNormalizer:
        """Build one immutable normalizer from a validated code-search policy.

        Parameters
        ----------
        policy
            Exact loaded curriculum-profile code-search policy.

        Returns
        -------
        CodeNormalizer
            Profile-governed deterministic normalizer.

        Raises
        ------
        CatalogError
            If configured delimiters collapse to empty or duplicate normalized values.
        """

        normalized_delimiters = tuple(
            _normalize_delimiter(
                case_sensitive=policy.case_sensitive,
                delimiter=delimiter,
                whitespace_normalization=policy.whitespace_normalization,
            )
            for delimiter in policy.prefix_delimiters
        )

        if any(not delimiter for delimiter in normalized_delimiters):
            raise CatalogError(
                details={"prefix_delimiters": policy.prefix_delimiters},
                message=(
                    "A configured code-prefix delimiter normalizes to an empty value."
                ),
            )

        if len(normalized_delimiters) != len(set(normalized_delimiters)):
            raise CatalogError(
                details={"prefix_delimiters": policy.prefix_delimiters},
                message=(
                    "Configured code-prefix delimiters normalize to duplicate values."
                ),
            )

        delimiter_pairs = [
            (delimiter, delimiter) for delimiter in normalized_delimiters
        ]
        delimiter_pairs.sort(key=_delimiter_pair_order_key)

        return cls(
            case_sensitive=policy.case_sensitive,
            normalized_delimiters=tuple(pair[1] for pair in delimiter_pairs),
            punctuation_normalization=policy.punctuation_normalization,
            source_delimiters=tuple(pair[0] for pair in delimiter_pairs),
            whitespace_normalization=policy.whitespace_normalization,
        )

    def is_prefix_match(self, *, candidate: str, prefix: str) -> bool:
        """Return whether a normalized code equals or descends from a prefix boundary.

        Parameters
        ----------
        candidate
            Normalized candidate code from one package-local posting.
        prefix
            Normalized non-empty prefix query.

        Returns
        -------
        bool
            ``True`` for exact equality or a configured delimiter boundary.
        """

        if candidate == prefix:
            return True

        return any(
            candidate.startswith(prefix + delimiter)
            for delimiter in self.normalized_delimiters
        )

    def normalize(self, value: str) -> str:
        """Normalize one code while preserving exact configured delimiter sequences.

        Parameters
        ----------
        value
            Authored code or caller-supplied query.

        Returns
        -------
        str
            Deterministic profile-governed normalized code.

        Raises
        ------
        ValueError
            If normalization produces an empty code.
        """

        transformed = _apply_case_policy(
            case_sensitive=self.case_sensitive, value=normalize_nfkc(value)
        )

        if self.whitespace_normalization:
            transformed = "".join(
                character for character in transformed if not character.isspace()
            )

        normalized_parts: list[str] = []
        index = 0

        while index < len(transformed):
            matched_delimiter_index = self._matching_delimiter_index(
                index=index, value=transformed
            )

            if matched_delimiter_index is not None:
                normalized_parts.append(
                    self.normalized_delimiters[matched_delimiter_index]
                )
                index += len(self.source_delimiters[matched_delimiter_index])
                continue

            character = transformed[index]
            index += 1

            if self.whitespace_normalization and character.isspace():
                continue

            if self.punctuation_normalization and unicodedata.category(
                character
            ).startswith("P"):
                continue

            normalized_parts.append(character)

        normalized = "".join(normalized_parts)

        if not normalized:
            raise ValueError("Code normalization produced an empty value.")

        return normalized

    def normalize_prefix(self, value: str) -> str:
        """Normalize one prefix and remove trailing configured delimiters.

        Parameters
        ----------
        value
            Caller-supplied code-prefix query.

        Returns
        -------
        str
            Non-empty normalized prefix without trailing delimiters.

        Raises
        ------
        ValueError
            If normalization or trailing-delimiter removal produces an empty value.
        """

        normalized = self.normalize(value)
        changed = True

        while changed:
            changed = False

            for delimiter in self.normalized_delimiters:
                if normalized.endswith(delimiter):
                    normalized = normalized[: -len(delimiter)]
                    changed = True
                    break

        if not normalized:
            raise ValueError("Code-prefix normalization produced an empty value.")

        return normalized

    def _matching_delimiter_index(self, *, index: int, value: str) -> int | None:
        """Return the first longest configured delimiter beginning at one position.

        Parameters
        ----------
        index
            Current source-string position.
        value
            NFKC and case-policy transformed source string.

        Returns
        -------
        int | None
            Tuple index of the matching delimiter, or ``None`` when absent.
        """

        suffix = value[index:]

        for delimiter_index, delimiter in enumerate(self.source_delimiters):
            if suffix.startswith(delimiter):
                return delimiter_index

        return None


def _apply_case_policy(*, case_sensitive: bool, value: str) -> str:
    """Apply the exact profile case-sensitivity policy.

    Parameters
    ----------
    case_sensitive
        Whether source and query code case must be preserved.
    value
        NFKC-normalized code surface.

    Returns
    -------
    str
        Original value or Unicode-case-folded value.
    """

    return value if case_sensitive else value.casefold()


def _delimiter_pair_order_key(pair: tuple[str, str]) -> tuple[int, str, str]:
    """Return longest-first deterministic order for one delimiter pair.

    Parameters
    ----------
    pair
        Transformed source delimiter and normalized delimiter.

    Returns
    -------
    tuple[int, str, str]
        Longest-first source length followed by stable lexical ties.
    """

    return -len(pair[0]), pair[0], pair[1]


def _normalize_delimiter(
    *, case_sensitive: bool, delimiter: str, whitespace_normalization: bool
) -> str:
    """Normalize one configured delimiter while always preserving punctuation.

    Parameters
    ----------
    case_sensitive
        Whether delimiter case is preserved.
    delimiter
        Exact configured delimiter surface.
    whitespace_normalization
        Whether Unicode whitespace is removed.

    Returns
    -------
    str
        Deterministic normalized delimiter.
    """

    normalized = _apply_case_policy(
        case_sensitive=case_sensitive, value=normalize_nfkc(delimiter)
    )

    if whitespace_normalization:
        normalized = "".join(
            character for character in normalized if not character.isspace()
        )

    return normalized


def normalize_facet_value(value: str) -> str:
    """Normalize one controlled facet without erasing meaningful punctuation.

    Parameters
    ----------
    value
        Source or caller-supplied facet value.

    Returns
    -------
    str
        NFKC, case-folded, whitespace-collapsed facet key.
    """

    normalized = normalize_nfkc(value).casefold()
    return " ".join(normalized.split())


def normalize_lexical_text(value: str) -> tuple[str, ...]:
    """Normalize text into deterministic Unicode letter-number-mark tokens.

    Parameters
    ----------
    value
        Source description or lexical query.

    Returns
    -------
    tuple[str, ...]
        Ordered maximal token runs after NFKC and Unicode case folding.
    """

    normalized = normalize_nfkc(value).casefold()
    tokens: list[str] = []
    token_characters: list[str] = []

    for character in normalized:
        category_prefix = unicodedata.category(character)[0]

        if category_prefix in {"L", "M", "N"}:
            token_characters.append(character)
            continue

        if token_characters:
            tokens.append("".join(token_characters))
            token_characters.clear()

    if token_characters:
        tokens.append("".join(token_characters))

    return tuple(tokens)


def normalize_nfkc(value: str) -> str:
    """Apply Unicode NFKC through the standard positional-only API.

    Parameters
    ----------
    value
        Unicode source text.

    Returns
    -------
    str
        NFKC-normalized Unicode text.
    """

    return unicodedata.normalize("NFKC", value)
