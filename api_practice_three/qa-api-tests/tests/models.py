from pydantic import BaseModel , EmailStr

class User(BaseModel):
    id: str
    email: str
    lastName: str
    firstName: str
    middleName: str | None = None

class UserResponse(BaseModel):
    user: User

class MeResponse(BaseModel):
    id: str
    email: EmailStr
    lastName: str
    firstName: str
    middleName: str | None = None
