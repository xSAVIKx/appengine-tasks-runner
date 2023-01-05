from typing import Any

import pydantic


class HttpServiceResponse(pydantic.BaseModel):
    """A request to call a service."""

    body: pydantic.BaseModel | dict[str, Any] | str | bytes | None = pydantic.Field(
        default_factory=dict, title="Body", description="The HTTP response body payload."
    )
    """The response body payload."""

    headers: dict[str, str] = pydantic.Field(
        default_factory=dict, title="Headers", description="The HTTP request headers."
    )
    """The HTTP request headers."""

    status_code: int = pydantic.Field(
        title="HTTP Status", description="The response HTTP status code."
    )
    """The response HTTP status code."""
