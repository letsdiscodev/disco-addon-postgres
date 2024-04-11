from typing import Callable

import requests


class KeyValueStore:
    def __init__(self, api_key: str, project_name: str):
        self._keyvalues: dict[str, str | None] = {}
        self._api_key = api_key
        self._project_name = project_name

    def get(self, key: str) -> str | None:
        url = f"http://disco/projects/{self._project_name}/keyvalues/{key}"
        response = requests.get(
            url,
            auth=(self._api_key, ""),
            headers={"Accept": "application/json"},
            timeout=10,
        )
        if response.status_code not in [200, 404]:
            raise Exception(f"Disco returned {response.status_code}: {response.text}")
        if response.status_code == 404:
            return None
        value = response.json()["value"]
        self._keyvalues[key] = value
        return value

    def set(self, key: str, value: str | None, raise_if_changed: bool = True) -> None:
        url = f"http://disco/projects/{self._project_name}/keyvalues/{key}"
        req_body: dict[str, str | None] = {"value": value}
        if raise_if_changed and key in self._keyvalues:
            req_body["previousValue"] = self._keyvalues[key]
        response = requests.put(
            url,
            auth=(self._api_key, ""),
            json=req_body,
            headers={"Accept": "application/json"},
            timeout=10,
        )
        if response.status_code != 200:
            raise Exception(f"Disco returned {response.status_code}: {response.text}")

    def update(
        self, key: str, update_func: Callable[[str | None], str], attempts: int = 5
    ) -> None:
        for i in range(attempts):
            try:
                value = self.get(key)
                new_value: str | None = update_func(value)
                self.set(key, new_value)
                break
            except Exception:
                if i == attempts - 1:
                    raise
