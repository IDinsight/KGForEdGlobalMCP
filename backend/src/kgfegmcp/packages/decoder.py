"""This module contains functionalities for parsing delivery JSONL and decoding wire
records into semantic graph models.

This module is the only boundary layer that knows the slim delivery format stores
selected semantic values inside strings. It reads one physical JSONL line at a time,
validates strict wire envelopes, decodes exact string booleans and embedded JSON
arrays, and preserves all raw properties. It does not compare identifiers, resolve
endpoints, validate topology, repair records, or establish graph-wide invariants.
"""

# Standard Library
import json

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from io import BytesIO
from math import isfinite
from pathlib import Path
from typing import BinaryIO, Generic, NoReturn, TypeAlias, TypeVar

# Third Party Library
from pydantic import BaseModel, ValidationError

# Package Library
from kgfegmcp.errors import DeliveryPropertyDecodingError, JSONLParsingError
from kgfegmcp.graph.models import (
    FrameworkNode,
    GraphRelationship,
    LearningComponentNode,
    StandardNode,
)
from kgfegmcp.packages.wire import (
    DELIVERY_SCHEMA_1_0_FRAMEWORK_LABEL,
    DELIVERY_SCHEMA_1_0_ITEM_LABEL,
    DELIVERY_SCHEMA_1_1_COMPONENT_LABEL,
    NodeWireEnvelope,
    RelationshipWireEnvelope,
)

GraphNodeT: TypeAlias = FrameworkNode | LearningComponentNode | StandardNode
JSONLSource: TypeAlias = Path | bytes
WireEnvelopeT = TypeVar("WireEnvelopeT", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class LocatedWireRecord(Generic[WireEnvelopeT]):
    """Associate a validated wire envelope with its source location and order.

    Attributes
    ----------
    line_number
        One-based physical line number in the JSONL artifact.
    record
        Validated node or relationship wire envelope.
    source_export_order
        Deterministic one-based order inherited from the physical JSONL line.
    source_path
        Internal path used for diagnostics; public errors expose only the file name.
    """

    line_number: int
    record: WireEnvelopeT
    source_export_order: int
    source_path: Path


def _decode_optional_boolean(
    *, line_number: int, path: Path, property_name: str, value: str | None
) -> bool | None:
    """Decode an optional boolean from the exact strings ``true`` and ``false``.

    Parameters
    ----------
    line_number
        One-based physical JSONL line number.
    path
        Internal path to the JSONL artifact.
    property_name
        Original delivery property name.
    value
        Raw optional string value.

    Returns
    -------
    bool | None
        Decoded boolean, or ``None`` when the property was omitted.

    Raises
    ------
    DeliveryPropertyDecodingError
        If the value is not exactly ``"true"`` or ``"false"``.
    """

    if value is None:
        return None

    if value == "true":
        return True

    if value == "false":
        return False

    _raise_property_decoding_error(
        line_number=line_number,
        path=path,
        property_name=property_name,
        reason='expected the exact string "true" or "false".',
    )


def _decode_optional_confidence(
    *, line_number: int, path: Path, property_name: str, value: str | None
) -> float | None:
    """Decode an optional confidence encoded as a delivery-property string.

    Parameters
    ----------
    line_number
        One-based physical JSONL line number.
    path
        Internal path to the JSONL artifact.
    property_name
        Original delivery property name.
    value
        Raw optional string value.

    Returns
    -------
    float | None
        Decoded confidence, or ``None`` when the property was omitted.

    Raises
    ------
    DeliveryPropertyDecodingError
        If the value is not a finite decimal between zero and one inclusive.
    """

    if value is None:
        return None

    try:
        decoded_value = float(value)
    except ValueError:
        _raise_property_decoding_error(
            line_number=line_number,
            path=path,
            property_name=property_name,
            reason="expected a decimal number encoded as a string.",
        )

    if not isfinite(decoded_value) or not 0.0 <= decoded_value <= 1.0:
        _raise_property_decoding_error(
            line_number=line_number,
            path=path,
            property_name=property_name,
            reason="expected a finite value between 0 and 1 inclusive.",
        )

    return decoded_value


def _decode_optional_string_array(
    *, line_number: int, path: Path, property_name: str, value: str | None
) -> tuple[str, ...] | None:
    """Decode an optional JSON array embedded in a delivery-property string.

    Parameters
    ----------
    line_number
        One-based physical JSONL line number.
    path
        Internal path to the JSONL artifact.
    property_name
        Original delivery property name.
    value
        Raw optional string containing a JSON array.

    Returns
    -------
    tuple[str, ...] | None
        Decoded strings in source order, or ``None`` when the property was omitted.

    Raises
    ------
    DeliveryPropertyDecodingError
        If the string is invalid JSON, does not contain an array, or contains a
        non-string array element.
    """

    if value is None:
        return None

    try:
        decoded_value = json.loads(value)
    except json.JSONDecodeError as error:
        _raise_property_decoding_error(
            line_number=line_number,
            path=path,
            property_name=property_name,
            reason=f"expected a JSON array encoded as a string ({error.msg}).",
        )

    if not isinstance(decoded_value, list):
        _raise_property_decoding_error(
            line_number=line_number,
            path=path,
            property_name=property_name,
            reason="expected a JSON array encoded as a string.",
        )

    if any(not isinstance(item, str) for item in decoded_value):
        _raise_property_decoding_error(
            line_number=line_number,
            path=path,
            property_name=property_name,
            reason="expected every decoded array element to be a string.",
        )

    return tuple(decoded_value)


def _iter_stream_wire_records(
    *, model_type: type[WireEnvelopeT], path: Path, stream: BinaryIO
) -> Iterator[LocatedWireRecord[WireEnvelopeT]]:
    """Validate one wire envelope per physical line from an open binary stream.

    Parameters
    ----------
    model_type
        Pydantic wire-envelope class used to validate each decoded JSON value.
    path
        Logical source path used for safe diagnostics.
    stream
        Open binary stream positioned at the beginning of the JSONL content.

    Yields
    ------
    LocatedWireRecord[WireEnvelopeT]
        Validated envelope with file, line, and deterministic export-order context.

    Raises
    ------
    JSONLParsingError
        If a line is not UTF-8 or valid JSON, or a decoded value does not satisfy the
        requested wire-envelope schema.
    """

    for line_number, raw_line in enumerate(stream, start=1):
        try:
            text = raw_line.decode("utf-8")
        except UnicodeDecodeError:
            _raise_jsonl_parsing_error(
                line_number=line_number, path=path, reason="line is not valid UTF-8."
            )

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            _raise_jsonl_parsing_error(
                line_number=line_number,
                path=path,
                reason=f"invalid JSON ({error.msg}).",
            )

        try:
            record = model_type.model_validate(payload)
        except ValidationError as error:
            _raise_jsonl_parsing_error(
                line_number=line_number,
                path=path,
                reason="record does not match the required wire envelope.",
                validation_errors=error.errors(include_input=False, include_url=False),
            )

        yield LocatedWireRecord(
            line_number=line_number,
            record=record,
            source_export_order=line_number,
            source_path=path,
        )


def _iter_wire_records(
    *, model_type: type[WireEnvelopeT], source: JSONLSource, source_path: Path | None
) -> Iterator[LocatedWireRecord[WireEnvelopeT]]:
    """Read and validate one wire envelope per physical JSONL line.

    Parameters
    ----------
    model_type
        Pydantic wire-envelope class used to validate each decoded JSON value.
    source
        JSONL artifact path or exact already-verified artifact bytes.
    source_path
        Logical source path used for diagnostics when ``source`` contains bytes.

    Yields
    ------
    LocatedWireRecord[WireEnvelopeT]
        Validated envelope with file, line, and deterministic export-order context.

    Raises
    ------
    JSONLParsingError
        If the file cannot be read, a line is not UTF-8 or valid JSON, or a decoded
        value does not satisfy the requested wire-envelope schema.
    ValueError
        If exact bytes are supplied without a logical diagnostic path.
    """

    if isinstance(source, Path):
        path = source

        try:
            with source.open("rb") as stream:
                yield from _iter_stream_wire_records(
                    model_type=model_type, path=path, stream=stream
                )
        except OSError:
            _raise_jsonl_parsing_error(
                line_number=None, path=path, reason="artifact could not be read."
            )

        return

    if source_path is None:
        raise ValueError("A logical source_path is required for in-memory JSONL bytes.")

    with BytesIO(source) as stream:
        yield from _iter_stream_wire_records(
            model_type=model_type, path=source_path, stream=stream
        )


def _raise_jsonl_parsing_error(
    *,
    line_number: int | None,
    path: Path,
    reason: str,
    validation_errors: Sequence[object] | None = None,
) -> NoReturn:
    """Raise a typed parsing error without exposing the full local path publicly.

    Parameters
    ----------
    line_number
        One-based line number, or ``None`` when the artifact could not be opened.
    path
        Internal path to the JSONL artifact.
    reason
        Concise public explanation of the parsing failure.
    validation_errors
        Optional structured Pydantic errors for internal diagnostics.

    Raises
    ------
    JSONLParsingError
        Always raised with public file-name context and internal path details.
    """

    line_context = "" if line_number is None else f" at line {line_number}"
    details: dict[str, object] = {
        "file_path": str(path),
        "line_number": line_number,
        "reason": reason,
    }

    if validation_errors is not None:
        details["validation_errors"] = list(validation_errors)

    raise JSONLParsingError(
        details=details,
        message=f"Could not parse '{path.name}'{line_context}: {reason}",
    )


def _raise_property_decoding_error(
    *, line_number: int, path: Path, property_name: str, reason: str
) -> NoReturn:
    """Raise a typed property-decoding error with safe source context.

    Parameters
    ----------
    line_number
        One-based physical JSONL line number.
    path
        Internal path to the JSONL artifact.
    property_name
        Original delivery property name.
    reason
        Concise explanation of the required encoding.

    Raises
    ------
    DeliveryPropertyDecodingError
        Always raised for the malformed encoded property.
    """

    raise DeliveryPropertyDecodingError(
        details={
            "file_path": str(path),
            "line_number": line_number,
            "property_name": property_name,
            "reason": reason,
        },
        message=(
            f"Could not decode property '{property_name}' in '{path.name}' at line "
            f"{line_number}: {reason}"
        ),
    )


def _raise_record_decoding_error(
    *,
    line_number: int,
    path: Path,
    reason: str,
    validation_errors: Sequence[object] | None = None,
) -> NoReturn:
    """Raise a typed semantic-record decoding error with safe source context.

    Parameters
    ----------
    line_number
        One-based physical JSONL line number.
    path
        Internal path to the JSONL artifact.
    reason
        Concise public explanation of the conversion failure.
    validation_errors
        Optional structured Pydantic errors for internal diagnostics.

    Raises
    ------
    DeliveryPropertyDecodingError
        Always raised for the record conversion failure.
    """

    details: dict[str, object] = {
        "file_path": str(path),
        "line_number": line_number,
        "reason": reason,
    }

    if validation_errors is not None:
        details["validation_errors"] = list(validation_errors)

    raise DeliveryPropertyDecodingError(
        details=details,
        message=(
            f"Could not decode record in '{path.name}' at line {line_number}: {reason}"
        ),
    )


def decode_node_record(
    located_record: LocatedWireRecord[NodeWireEnvelope],
) -> GraphNodeT:
    """Decode one validated node envelope into a semantic graph-node model.

    Parameters
    ----------
    located_record
        Validated node envelope with file and line context.

    Returns
    -------
    FrameworkNode | LearningComponentNode | StandardNode
        Immutable semantic node retaining all raw property strings.

    Raises
    ------
    DeliveryPropertyDecodingError
        If encoded properties are malformed, labels cannot identify one supported node
        kind, or typed semantic fields fail validation.
    """

    envelope = located_record.record
    properties = envelope.properties
    labels = tuple(envelope.labels)
    is_component = DELIVERY_SCHEMA_1_1_COMPONENT_LABEL in labels
    is_framework = DELIVERY_SCHEMA_1_0_FRAMEWORK_LABEL in labels
    is_standard = DELIVERY_SCHEMA_1_0_ITEM_LABEL in labels
    is_current = _decode_optional_boolean(
        line_number=located_record.line_number,
        path=located_record.source_path,
        property_name="isCurrent",
        value=properties.is_current,
    )

    if (is_component + is_framework + is_standard) != 1:
        _raise_record_decoding_error(
            line_number=located_record.line_number,
            path=located_record.source_path,
            reason=(
                "node labels must identify exactly one standards framework, standards "
                "framework item, or learning component."
            ),
        )

    try:
        if is_framework:
            return FrameworkNode(
                academic_subject=properties.academic_subject,
                adoption_status=properties.adoption_status,
                attribution_statement=properties.attribution_statement,
                author=properties.author,
                case_identifier_uri=properties.case_identifier_uri,
                case_identifier_uuid=properties.case_identifier_uuid,
                in_language=properties.in_language,
                is_current=is_current,
                jurisdiction=properties.jurisdiction,
                labels=labels,
                license=properties.license,
                name=properties.name,
                node_id=envelope.identifier,
                property_identifier=properties.identifier,
                provider=properties.provider,
                source_export_order=located_record.source_export_order,
            )

        if is_component:
            return LearningComponentNode(
                academic_subject=properties.academic_subject,
                adoption_status=properties.adoption_status,
                attribution_statement=properties.attribution_statement,
                author=properties.author,
                case_identifier_uri=properties.case_identifier_uri,
                case_identifier_uuid=properties.case_identifier_uuid,
                description=properties.description,
                identity_key=properties.identity_key,
                in_language=properties.in_language,
                is_current=is_current,
                jurisdiction=properties.jurisdiction,
                labels=labels,
                license=properties.license,
                node_id=envelope.identifier,
                property_identifier=properties.identifier,
                provider=properties.provider,
                source_export_order=located_record.source_export_order,
                tags=_decode_optional_string_array(
                    line_number=located_record.line_number,
                    path=located_record.source_path,
                    property_name="tags",
                    value=properties.tags,
                ),
            )

        grade_level = _decode_optional_string_array(
            line_number=located_record.line_number,
            path=located_record.source_path,
            property_name="gradeLevel",
            value=properties.grade_level,
        )
        return StandardNode(
            academic_subject=properties.academic_subject,
            adoption_status=properties.adoption_status,
            attribution_statement=properties.attribution_statement,
            author=properties.author,
            case_identifier_uri=properties.case_identifier_uri,
            case_identifier_uuid=properties.case_identifier_uuid,
            description=properties.description,
            grade_level=grade_level,
            in_language=properties.in_language,
            is_current=is_current,
            jurisdiction=properties.jurisdiction,
            labels=labels,
            license=properties.license,
            node_id=envelope.identifier,
            normalized_statement_type=properties.normalized_statement_type,
            property_identifier=properties.identifier,
            provider=properties.provider,
            source_export_order=located_record.source_export_order,
            statement_code=properties.statement_code,
            statement_type=properties.statement_type,
        )
    except ValidationError as error:
        _raise_record_decoding_error(
            line_number=located_record.line_number,
            path=located_record.source_path,
            reason="typed node fields are invalid.",
            validation_errors=error.errors(include_input=False, include_url=False),
        )


def decode_relationship_record(
    located_record: LocatedWireRecord[RelationshipWireEnvelope],
) -> GraphRelationship:
    """Decode one validated relationship envelope without resolving endpoints.

    Parameters
    ----------
    located_record
        Validated relationship envelope with file and line context.

    Returns
    -------
    GraphRelationship
        Immutable semantic relationship retaining outer and property endpoints.

    Raises
    ------
    DeliveryPropertyDecodingError
        If typed semantic fields fail validation.
    """

    envelope = located_record.record
    properties = envelope.properties

    try:
        return GraphRelationship(
            attribution_statement=properties.attribution_statement,
            author=properties.author,
            description=properties.description,
            label=envelope.label,
            license=properties.license,
            property_identifier=properties.identifier,
            provider=properties.provider,
            relationship_id=envelope.identifier,
            relationship_type=properties.relationship_type,
            resolution_status=properties.resolution_status,
            source_entity=properties.source_entity,
            source_entity_key=properties.source_entity_key,
            source_entity_value=properties.source_entity_value,
            source_export_order=located_record.source_export_order,
            source_labels=tuple(envelope.source_labels),
            source_node_id=envelope.source_identifier,
            support_confidence=_decode_optional_confidence(
                line_number=located_record.line_number,
                path=located_record.source_path,
                property_name="supportConfidence",
                value=properties.support_confidence,
            ),
            target_entity=properties.target_entity,
            target_entity_key=properties.target_entity_key,
            target_entity_value=properties.target_entity_value,
            target_labels=tuple(envelope.target_labels),
            target_node_id=envelope.target_identifier,
        )
    except ValidationError as error:
        _raise_record_decoding_error(
            line_number=located_record.line_number,
            path=located_record.source_path,
            reason="typed relationship fields are invalid.",
            validation_errors=error.errors(include_input=False, include_url=False),
        )


def iter_decoded_nodes(
    *, source: JSONLSource, source_path: Path | None = None
) -> Iterator[GraphNodeT]:
    """Parse and decode every node record from a JSONL artifact lazily.

    Parameters
    ----------
    source
        Path to a node delivery artifact or its exact already-verified bytes.
    source_path
        Logical source path used for diagnostics when ``source`` contains bytes.

    Yields
    ------
    FrameworkNode | LearningComponentNode | StandardNode
        One semantic node per physical source line.
    """

    for located_record in iter_node_wire_records(
        source=source, source_path=source_path
    ):
        yield decode_node_record(located_record)


def iter_decoded_relationships(
    *, source: JSONLSource, source_path: Path | None = None
) -> Iterator[GraphRelationship]:
    """Parse and decode every relationship record from a JSONL artifact lazily.

    Parameters
    ----------
    source
        Path to a relationship delivery artifact or its exact verified bytes.
    source_path
        Logical source path used for diagnostics when ``source`` contains bytes.

    Yields
    ------
    GraphRelationship
        One semantic relationship per physical source line.
    """

    for located_record in iter_relationship_wire_records(
        source=source, source_path=source_path
    ):
        yield decode_relationship_record(located_record)


def iter_node_wire_records(
    *, source: JSONLSource, source_path: Path | None = None
) -> Iterator[LocatedWireRecord[NodeWireEnvelope]]:
    """Parse a node JSONL artifact into located strict wire envelopes.

    Parameters
    ----------
    source
        Path to a node delivery artifact or its exact already-verified bytes.
    source_path
        Logical source path used for diagnostics when ``source`` contains bytes.

    Yields
    ------
    LocatedWireRecord[NodeWireEnvelope]
        One validated node envelope per physical source line.
    """

    yield from _iter_wire_records(
        model_type=NodeWireEnvelope, source=source, source_path=source_path
    )


def iter_relationship_wire_records(
    *, source: JSONLSource, source_path: Path | None = None
) -> Iterator[LocatedWireRecord[RelationshipWireEnvelope]]:
    """Parse a relationship JSONL artifact into located strict wire envelopes.

    Parameters
    ----------
    source
        Path to a relationship delivery artifact or its exact verified bytes.
    source_path
        Logical source path used for diagnostics when ``source`` contains bytes.

    Yields
    ------
    LocatedWireRecord[RelationshipWireEnvelope]
        One validated relationship envelope per physical source line.
    """

    yield from _iter_wire_records(
        model_type=RelationshipWireEnvelope, source=source, source_path=source_path
    )
