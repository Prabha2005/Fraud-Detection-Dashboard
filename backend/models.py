from pydantic import BaseModel

class Transaction(BaseModel):
    amount: float
    time: int
    location: str

class LoginRequest(BaseModel):
    username: str
    password: str