from typing import Any, List
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    loc: List[str | int]
    msg: str
    type: str

class ErrorResponse(BaseModel):
    error: str
    details: List[ErrorDetail] | None = None

class APIException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)
