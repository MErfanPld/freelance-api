from pydantic import BaseModel, ConfigDict, Field


class CredentialCreate(BaseModel):
    project_id: str
    title: str = Field(min_length=1, max_length=200)
    username: str | None = Field(
        default=None,
        max_length=200,
    )
    password: str = Field(
        min_length=1,
        max_length=1000,
    )
    website: str | None = Field(
        default=None,
        max_length=500,
    )
    notes: str | None = None


class CredentialUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    username: str | None = Field(
        default=None,
        max_length=200,
    )
    password: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )
    website: str | None = Field(
        default=None,
        max_length=500,
    )
    notes: str | None = None


class CredentialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    username: str | None
    website: str | None
    notes: str | None


class CredentialRevealResponse(CredentialResponse):
    password: str


class CredentialListResponse(BaseModel):
    items: list[CredentialResponse]
    total: int
    page: int
    page_size: int
    pages: int
