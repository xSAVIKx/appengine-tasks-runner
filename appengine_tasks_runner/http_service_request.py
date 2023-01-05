from typing import Any

import pydantic


class HttpServiceRequest(pydantic.BaseModel):
    """A request to call a service."""

    url: pydantic.AnyHttpUrl = pydantic.Field(
        title="URL", description="The URL of a service to be called."
    )
    """The URL of a service to be called."""

    body: pydantic.BaseModel | dict[str, Any] | str | bytes = pydantic.Field(
        default_factory=dict, title="Body", description="The HTTP request body payload."
    )
    """The request body payload."""

    content_type: str = pydantic.Field(
        default="application/json",
        title="Content Type",
        description="The HTTP request body content type. Defaults to JSON.",
    )
    """The HTTP request body content type. Defaults to JSON."""

    method: str = pydantic.Field(
        default="POST", title="Method", description="The HTTP request method."
    )
    """The HTTP request content type."""

    headers: dict[str, str] = pydantic.Field(
        default_factory=dict, title="Headers", description="The HTTP request headers."
    )
    """The HTTP request headers."""

    timeout: float = pydantic.Field(
        default=43200, title="Timeout", description="The request timeout in seconds."
    )
    """The request timeout in seconds."""

    class Config(pydantic.BaseConfig):
        """Model configuration."""

        smart_union = True
        """Ensures that Pydantic is able to distinguish between `Model` and `dict`.

        See https://pydantic-docs.helpmanual.io/usage/types/#unions for additional details.
        """
