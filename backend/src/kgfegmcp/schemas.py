"""This module contains shared Pydantic schema configuration for the backend."""

# Third Party Library
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """Base model for strict, alias-aware backend contracts.

    Models use Pythonic snake_case internally while accepting and serializing stable
    lower-camel-case field aliases at configuration and MCP boundaries.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        validate_default=True,
    )


class FrozenSchema(BaseSchema):
    """Base model for immutable validated backend contracts."""

    model_config = ConfigDict(frozen=True)
