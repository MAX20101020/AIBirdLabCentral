from pydantic import BaseModel, EmailStr, Field

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=32)

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=32)
    name: str = Field(min_length=3, max_length=20, examples=["Максим"])

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    model_config = {
        "from_attributes": True
    }

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse