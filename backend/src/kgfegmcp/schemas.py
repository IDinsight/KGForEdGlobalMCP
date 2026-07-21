"""This module contains top-level Pydantic models."""

# Third Party Library
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base model for all schemas."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)
