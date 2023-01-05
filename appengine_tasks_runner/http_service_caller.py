import json
import os
from typing import Final

import pydantic
import requests
from google.auth.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

from appengine_tasks_runner import HttpServiceRequest, HttpServiceResponse


class HttpServiceCaller:
    """Provides APIs for securely calling GCP services which require OIDC authentication
    such as Cloud Functions or Cloud Run."""

    SERVICE_CALLER_SECRET_ENV: Final[str] = "SERVICE_CALLER_SECRET"
    """The name of the environment variable which holds the the Service Invoker secret.

    The secret is expected to be a JSON string with the service account private key info.
    """

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
        self._service_invoker_credentials: dict = self._prepare_credentials(
            service_caller_credentials
        )

    def _prepare_credentials(self, service_invoker_credentials: dict | None = None) -> dict:
        if service_invoker_credentials:
            return service_invoker_credentials
        service_invoker_credentials_json = os.getenv(HttpServiceCaller.SERVICE_CALLER_SECRET_ENV)
        if service_invoker_credentials_json:
            res: dict = json.loads(service_invoker_credentials_json)
            return res
        raise RuntimeError(
            "Service caller credentials are not configured. Please set the "
            f"`{HttpServiceCaller.SERVICE_CALLER_SECRET_ENV}` environment variable."
        )

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

    def call_api(self, request: HttpServiceRequest) -> HttpServiceResponse:
        """Calls a GCP API available at the request `url` with an HTTP request.

        The request is authenticated using OAuth2 token.

        Args:
            request: The request to be sent.
        Returns:
            The HTTP response.
        Raises:
            HttpCallFailed: When the HTTP call to the API has failed.
            MaxHttpRetryError: When HTTP call has gotten too many repeatable failing responses.
        """
        session: AuthorizedSession = self._api_auth_session()
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
            body=response.content, headers=response.headers, status_code=response.status_code
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

    def _api_auth_session(self) -> AuthorizedSession:
        credentials: Credentials = self._sa_credentials()
        return AuthorizedSession(credentials)

    def _sa_credentials(self) -> Credentials:
        return service_account.Credentials.from_service_account_info(
            info=self._service_invoker_credentials,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

    def _service_auth_session(self, target_service: str) -> AuthorizedSession:
        credentials: Credentials = self._sa_token_credentials(target_service)
        return AuthorizedSession(credentials)

    def _sa_token_credentials(self, target_service: str) -> Credentials:
        return service_account.IDTokenCredentials.from_service_account_info(
            self._service_invoker_credentials, target_audience=target_service
        )
