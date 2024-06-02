import os

addon_project_name = os.environ.get("DISCO_PROJECT_NAME")
api_key = os.environ.get("DISCO_API_KEY")
disco_host = os.environ.get("DISCO_HOST")
assert addon_project_name is not None
assert api_key is not None
assert disco_host is not None
