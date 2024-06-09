import os

from fastapi import HTTPException

addon_project_name = os.environ.get("DISCO_PROJECT_NAME")

disco_host = os.environ.get("DISCO_HOST")
assert addon_project_name is not None
assert disco_host is not None


def get_api_key():
    api_key = os.environ.get("DISCO_API_KEY")
    if api_key is None:
        raise HTTPException(
            422,
            "API key not provided, please update your CLI by running 'disco update'",
        )
    yield api_key
