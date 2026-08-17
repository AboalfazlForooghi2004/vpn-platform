from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentOperation(StrEnum):
    CREATE_PEER = "CREATE_PEER"
    ENABLE_PEER = "ENABLE_PEER"
    DISABLE_PEER = "DISABLE_PEER"
    DELETE_PEER = "DELETE_PEER"
    READ_COUNTERS = "READ_COUNTERS"
    HEALTH = "HEALTH"


class AgentRequest(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    idempotency_key: str
    operation: AgentOperation
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    request_id: UUID
    ok: bool
    result: dict[str, Any] = Field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None
