import os

from addon.keyvaluestore import KeyValueStore

addon_project_name = os.environ.get("DISCO_PROJECT_NAME")
api_key = os.environ.get("DISCO_API_KEY")
disco_host = os.environ.get("DISCO_HOST")
assert addon_project_name is not None
assert api_key is not None
assert disco_host is not None

store = KeyValueStore(api_key=api_key, project_name=addon_project_name)
