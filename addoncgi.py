#!/usr/bin/env python3

import logging

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)

log.info("Handling CGI request from Postgres addon")


def main():
    from a2wsgi import ASGIMiddleware
    from wsgiref.handlers import CGIHandler

    from addon.api import app
    from addon.exchandler import stderr_traceback_on_exception

    app.add_exception_handler(Exception, stderr_traceback_on_exception)

    wsgi_application = ASGIMiddleware(app)  # type: ignore
    CGIHandler().run(wsgi_application)  # type: ignore


if __name__ == "__main__":
    main()
