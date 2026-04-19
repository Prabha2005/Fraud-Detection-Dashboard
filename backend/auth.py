import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "mysecretkey"
security = HTTPBearer()

# ✅ CREATE TOKEN
def create_token(username: str):
    return jwt.encode({"user": username}, SECRET_KEY, algorithm="HS256")

# ✅ VERIFY TOKEN
def verify_token(token: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")