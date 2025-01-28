import copy
import logging
from typing import Any

import requests

from addon import misc

log = logging.getLogger(__name__)


def create_postgres_project(api_key: str) -> str:
    log.info("Creating Postgres project")
    assert api_key is not None
    req_body = {
        "name": "postgres-instance",
        "generateSuffix": True,
    }
    response = requests.post(
        "http://disco/api/projects",
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    misc.assert_status_code(response, 201)
    project_name = response.json()["project"]["name"]
    log.info("Created Postgres project %s", project_name)
    return project_name


def remove_project(project_name: str, api_key: str) -> None:
    log.info("Removing Postgres project %s", project_name)
    assert api_key is not None
    response = requests.delete(
        f"http://disco/api/projects/{project_name}",
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    misc.assert_status_code(response, 200)


def init_postgres_env_variables(
    postgres_project_name: str, admin_user: str, admin_password: str, api_key: str
) -> None:
    log.info("Setting env vars for Postgres before starting it")
    assert api_key is not None
    url = f"http://disco/api/projects/{postgres_project_name}/env"
    req_body = dict(
        envVariables=[
            {
                "name": "POSTGRES_USER",
                "value": admin_user,
            },
            {
                "name": "POSTGRES_PASSWORD",
                "value": admin_password,
            },
            {
                "name": "PGDATA",
                "value": "/var/lib/postgresql/data/pgdata",
            },
        ],
    )
    response = requests.post(
        url,
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    misc.assert_status_code(response, 200)


POSTGRES_DISCO_FILE = {
    "version": "1.0",
    "services": {
        "postgres": {
            "image": "postgres:16.1",
            "exposedInternally": True,
            "volumes": [
                {"name": "postgres-data", "destinationPath": "/var/lib/postgresql/data"}
            ],
        }
    },
}


def deploy_postgres_project(
    postgres_project_name: str, image: str, version: str, api_key: str
) -> int:
    log.info("Deploying Postgres %s (%s)", postgres_project_name, version)
    assert api_key is not None
    url = f"http://disco/api/projects/{postgres_project_name}/deployments"
    disco_file: dict[str, Any] = copy.deepcopy(POSTGRES_DISCO_FILE)
    disco_file["services"]["postgres"]["image"] = f"{image}:{version}"
    req_body = {
        "discoFile": disco_file,
    }
    response = requests.post(
        url,
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    misc.assert_status_code(response, 201)
    resp_body = response.json()
    return resp_body["deployment"]["number"]


def project_exists(project_name: str, api_key: str):
    assert api_key is not None
    response = requests.get(
        "http://disco/api/projects",
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    misc.assert_status_code(response, 200)
    return project_name in [project["name"] for project in response.json()["projects"]]


def set_conn_str_env_var(
    project_name: str,
    var_name: str,
    conn_str: str,
    api_key: str,
) -> int | None:
    log.info("Setting connection string env variable %s for %s", var_name, project_name)
    assert api_key is not None
    url = f"http://disco/api/projects/{project_name}/env"
    req_body = dict(
        envVariables=[
            {
                "name": var_name,
                "value": conn_str,
            }
        ],
    )
    response = requests.post(
        url,
        json=req_body,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    misc.assert_status_code(response, 200)
    resp_body = response.json()
    if resp_body["deployment"] is None:
        return None
    return resp_body["deployment"]["number"]


def get_conn_str_env_var(
    project_name: str,
    var_name: str,
    api_key: str,
) -> str | None:
    log.info("Getting connection string env variable %s for %s", var_name, project_name)
    assert api_key is not None
    url = f"http://disco/api/projects/{project_name}/env/{var_name}"
    response = requests.get(
        url,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    if response.status_code == 404:
        return None
    return response.json()["envVariable"]["value"]


def unset_conn_str_env_var(
    project_name: str,
    var_name: str,
    api_key: str,
) -> int | None:
    log.info(
        "Unsetting connection string env variable %s for %s", var_name, project_name
    )
    assert api_key is not None
    url = f"http://disco/api/projects/{project_name}/env/{var_name}"
    response = requests.delete(
        url,
        auth=(api_key, ""),
        headers={"Accept": "application/json"},
        timeout=10,
    )
    misc.assert_status_code(response, 200)
    resp_body = response.json()
    if resp_body["deployment"] is None:
        return None
    return resp_body["deployment"]["number"]
