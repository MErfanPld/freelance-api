from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    company: str | None = Field(
        default=None,
        max_length=200,
    )
    email: EmailStr | None = None
    phone: str | None = Field(
        default=None,
        max_length=50,
    )
    address: str | None = None
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    company: str | None = Field(
        default=None,
        max_length=200,
    )
    email: EmailStr | None = None
    phone: str | None = Field(
        default=None,
        max_length=50,
    )
    address: str | None = None
    notes: str | None = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    company: str | None
    email: str | None
    phone: str | None
    address: str | None
    notes: str | None


class ClientListResponse(BaseModel):
    items: list[ClientResponse]
    total: int
    page: int
    page_size: int
    pages: int
