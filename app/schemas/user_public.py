from pydantic import BaseModel, ConfigDict


class PublicIdResponse(BaseModel):
    """Minimal response containing only the user's public UUID."""

    model_config = ConfigDict(from_attributes=True)

    id: str
