from pydantic import BaseModel, Field, HttpUrl, SecretStr


# Login details, only needed for authenticated testing
class LoginRequest(BaseModel):
    url: HttpUrl
    username: str = Field(min_length=1)
    password: SecretStr = Field(min_length=1)

    # Tell the crawler where to enter and submit the credentials
    username_selector: str = Field(min_length=1)
    password_selector: str = Field(min_length=1)
    submit_selector: str = Field(min_length=1)

    # Optional URL used to check whether login succeeded
    success_url: HttpUrl | None = None


# Details needed to start a test
class RunRequest(BaseModel):
    url: HttpUrl
    login: LoginRequest | None = None