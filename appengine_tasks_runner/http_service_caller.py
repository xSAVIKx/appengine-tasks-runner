import json
import os
from functools import cache
from typing import Final

import pydantic
import requests
from google.auth.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession
from google.cloud.secretmanager_v1 import (
    AccessSecretVersionRequest,
    AccessSecretVersionResponse,
    SecretManagerServiceClient,
    SecretPayload,
)
from google.oauth2 import service_account

from appengine_tasks_runner.http_service_request import HttpServiceRequest
from appengine_tasks_runner.http_service_response import HttpServiceResponse


@cache
def _load_secret(secret_name: str) -> str:
    """Loads content of the GCP secret by its name."""

    gcp_project: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not gcp_project:
        raise RuntimeError(
            "GCP project is not configured in `GOOGLE_CLOUD_PROJECT` env variable."
        )
    secret_path: str = f"projects/{gcp_project}/secrets/{secret_name}/versions/latest"
    request: AccessSecretVersionRequest = AccessSecretVersionRequest()
    request.name = secret_path
    secret_manager: SecretManagerServiceClient = SecretManagerServiceClient()
    secret_version: AccessSecretVersionResponse = secret_manager.access_secret_version(
        request=request
    )
    secret_payload: SecretPayload = secret_version.payload
    secret_data: bytes = secret_payload.data
    return secret_data.decode("utf-8")


class HttpServiceCaller:
    """Provides APIs for securely calling GCP services which require OIDC authentication
    such as Cloud Functions or Cloud Run."""

    SERVICE_CALLER_SECRET_ENV: Final[str] = "SERVICE_CALLER_SECRET"
    """The name of the environment variable which holds the the Service Invoker secret.

    The secret is expected to be a JSON string with the service account private key info.
    """

    SERVICE_CALLER_SECRET_NAME_ENV: Final[str] = "SERVICE_CALLER_SECRET_NAME"
    """The name of the environment variable which holds the name of the Service Caller secret."""

    def __init__(
        self,
        service_caller_credentials: dict | None = None,
    ):
        """Creates a new service caller with the provided credentials or the Secret Manager
        secret name to fetch the credentials.

        Args:
            service_caller_credentials: The credentials the caller should be using
                to authenticate the requests.
        Raises:
            RuntimeError: if no credentials were provided or the credentials secret name
                is not configured.
        """
        self._service_caller_credentials: dict = self._prepare_credentials(
            service_caller_credentials=service_caller_credentials
        )

    def _prepare_credentials(self, service_caller_credentials: dict | None = None) -> dict:
        if service_caller_credentials:
            return service_caller_credentials
        service_caller_credentials_json = os.getenv(HttpServiceCaller.SERVICE_CALLER_SECRET_ENV)
        if service_caller_credentials_json:
            return dict(json.loads(service_caller_credentials_json))
        secret_name = os.getenv(HttpServiceCaller.SERVICE_CALLER_SECRET_NAME_ENV)
        if not secret_name:
            raise RuntimeError(
                "Service caller credentials are not configured. Please set the "
                f"`{HttpServiceCaller.SERVICE_CALLER_SECRET_ENV}` or "
                f"`{HttpServiceCaller.SERVICE_CALLER_SECRET_NAME_ENV}` environment variables "
                "with either the credentials or the name of the secret which holds the credentials."
            )
        service_caller_credentials_json_secret: str = _load_secret(secret_name=secret_name)
        return dict(json.loads(service_caller_credentials_json_secret))

    def call_service(self, request: HttpServiceRequest) -> HttpServiceResponse:
        """Calls a GCP service available at the request `url` with an HTTP request.

        The request is authenticated using Open ID connect token.

        Args:
            request: The request to be sent.
        Returns:
            The HTTP response.
        Raises:
            HttpCallFailed: When the HTTP call to the service has failed.
            MaxHttpRetryError: When HTTP call has gotten too many repeatable failing responses.
        """
        session: AuthorizedSession = self._service_auth_session(request.url)
        res: HttpServiceResponse = self._do_call(request, session)
        return res

    def _do_call(
        self,
        request: HttpServiceRequest,
        auth_session: AuthorizedSession,
    ) -> HttpServiceResponse:
        """Does the actual HTTP call to a service or API."""

        headers: dict[str, str] = request.headers
        headers["content-type"] = request.content_type
        data: str | bytes | dict = self._prepare_request_content(request)
        response: requests.Response = auth_session.request(
            method=request.method,
            url=request.url,
            data=data,
            timeout=request.timeout,
            headers=headers,
        )
        return HttpServiceResponse(
            body=response.content,
            headers=dict(response.headers),
            status_code=response.status_code,
        )

    def _prepare_request_content(self, request: HttpServiceRequest) -> str | bytes | dict:
        """Ensures content type is set in the headers and request body is encoded."""
        data: str | bytes | dict = {}
        is_json = request.content_type == "application/json"
        match request.body:
            case dict():
                if is_json:
                    data = json.dumps(request.body, default=pydantic.BaseModel.__json_encoder__)
            case pydantic.BaseModel():
                if is_json:
                    data = request.body.json()
                else:
                    data = request.body.dict()
            case _:
                data = request.body
        return data

    def _service_auth_session(self, target_service: str) -> AuthorizedSession:
        credentials: Credentials = self._sa_token_credentials(target_service)
        return AuthorizedSession(credentials)

    def _sa_token_credentials(self, target_service: str) -> Credentials:
        return service_account.IDTokenCredentials.from_service_account_info(
            self._service_caller_credentials, target_audience=target_service
        )
