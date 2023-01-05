from fastapi import FastAPI

from appengine_tasks_runner import (
    HttpServiceCaller,
    HttpServiceRequest,
    HttpServiceResponse,
)

app = FastAPI()

service_caller: HttpServiceCaller = HttpServiceCaller()


@app.post("/")
async def handle_task(http_service_request: HttpServiceRequest) -> HttpServiceResponse:
    """Handles AppEngine HTTP Cloud Task requests.

    Sends the request content to the specified by the request URL service and returns
    back the response.
    """
    response: HttpServiceResponse = service_caller.call_service(request=http_service_request)
    return response


@app.get("/_ah/warmup")
async def warmup():
    """Handles AppEngine warmup requests."""
    return {"status": "OK"}
