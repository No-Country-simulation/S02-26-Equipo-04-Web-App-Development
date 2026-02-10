from app.schemas.base import BaseSchema

class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenPayload(BaseSchema):
    sub: str | None = None
