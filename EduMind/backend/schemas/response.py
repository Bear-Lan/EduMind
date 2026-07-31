"""
EduMind Standard Response Schemas

All API endpoints must use these response models.
See 06_API_Spec.md for the standard response format.
"""

from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """
    Unified API response format.

    Success: {"success": true, "code": 200, "message": "success", "data": {...}}
    Error:   {"success": false, "code": 400, "message": "error", "data": null}
    """

    success: bool
    code: int
    message: str
    data: Optional[T] = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "success") -> "StandardResponse":
        return cls(success=True, code=200, message=message, data=data)

    @classmethod
    def created(cls, data: Any = None, message: str = "created") -> "StandardResponse":
        return cls(success=True, code=201, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str) -> "StandardResponse":
        return cls(success=False, code=code, message=message, data=None)

    @classmethod
    def not_implemented(cls) -> "StandardResponse":
        return cls(
            success=False,
            code=501,
            message="Not implemented in this phase",
            data=None,
        )
