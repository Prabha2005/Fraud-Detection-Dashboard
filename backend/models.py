from pydantic import BaseModel, Field


class Transaction(BaseModel):
    amount: float = Field(gt=0)
    time: int = Field(ge=0, le=23)
    location: str | None = None
    device_change: int = Field(
        default=0,
        ge=0,
        le=1,
    )
    merchant_risk: float = Field(
        default=0.0,
        ge=0,
        le=1,
    )
    geo_velocity: float = Field(
        default=0.0,
        ge=0,
    )


class LoginRequest(BaseModel):
    username: str
    password: str