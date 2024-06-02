import logging

from fastapi import Request
from fastapi.responses import PlainTextResponse

log = logging.getLogger(__name__)


async def stderr_traceback_on_exception(
    request: Request, exc: Exception
) -> PlainTextResponse:
    log.exception("Error handling CGI request")
    return PlainTextResponse("Internal Error", status_code=500)
