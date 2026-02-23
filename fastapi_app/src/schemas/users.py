from pydantic import BaseModel, SecretStr, Field


class User(BaseModel):
    login: str
    password: SecretStr
