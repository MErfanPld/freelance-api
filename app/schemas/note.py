from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    project_id: str
    client_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)


class NoteUpdate(BaseModel):
    client_id: str | None = None
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    content: str | None = Field(
        default=None,
        min_length=1,
    )


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    client_id: str | None
    title: str
    content: str


class NoteListResponse(BaseModel):
    items: list[NoteResponse]
    total: int
    page: int
    page_size: int
    pages: int
