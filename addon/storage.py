from datetime import datetime, timezone
import json
from typing import Any
from addon.context import store
from addon import misc
import logging

log = logging.getLogger(__name__)

POSTGRES_PROJECT_NAMES_KEY = "POSTGRES_PROJECT_NAMES"
POSTGRES_META_KEY = "POSTGRES_META_{project_name}"


def get_postgres_project_names() -> list[str]:
    value = store.get(key=POSTGRES_PROJECT_NAMES_KEY)
    if value is None:
        return []
    return json.loads(value)


def add_postgres_instance(project_name: str, version: str) -> None:
    log.info("Saving info about new instance %s", project_name)

    def update_func(value: str | None) -> str:
        if value is None:
            names = []
        else:
            names = json.loads(value)
        names.append(project_name)
        new_value = json.dumps(names)
        return new_value

    store.update(key=POSTGRES_PROJECT_NAMES_KEY, update_func=update_func)
    meta: dict[str, Any] = {
        "created": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "admin": None,
        "databases": {},
    }
    store.set(
        key=POSTGRES_META_KEY.format(project_name=project_name), value=json.dumps(meta)
    )


def remove_postgres_instance(project_name: str) -> None:
    log.info("Removing info about instance %s", project_name)

    def update_func(value: str | None) -> str:
        if value is None:
            names = []
        else:
            names = json.loads(value)
        names.remove(project_name)
        new_value = json.dumps(names)
        return new_value

    store.update(key=POSTGRES_PROJECT_NAMES_KEY, update_func=update_func)
    store.unset(key=POSTGRES_META_KEY.format(project_name=project_name))


def get_instance(
    postgres_project_name: str,
) -> dict[str, Any] | None:
    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    value = store.get(key)
    if value is None:
        return None
    return json.loads(value)


def save_admin_credentials(
    postgres_project_name: str, user: str, password: str
) -> None:
    log.info("Saving admin credentials for %s", postgres_project_name)

    def update_func(value: str | None) -> str:
        assert value is not None
        meta = json.loads(value)
        meta["admin"] = {"user": user, "password": password}
        new_value = json.dumps(meta)
        return new_value

    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    store.update(key=key, update_func=update_func)


def add_db(
    postgres_project_name: str,
    db_name: str,
) -> None:
    log.info("Storing info about database %s (%s)", db_name, postgres_project_name)

    def update_func(value: str | None) -> str:
        assert value is not None
        meta = json.loads(value)
        meta["databases"][db_name] = {
            "created": datetime.now(timezone.utc).isoformat(),
            "users": {},
        }
        new_value = json.dumps(meta)
        return new_value

    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    store.update(key=key, update_func=update_func)


def remove_db(
    postgres_project_name: str,
    db_name: str,
) -> None:
    log.info("Removing info about database %s (%s)", db_name, postgres_project_name)

    def update_func(value: str | None) -> str:
        assert value is not None
        meta = json.loads(value)
        if db_name in meta["databases"]:
            del meta["databases"][db_name]
        new_value = json.dumps(meta)
        return new_value

    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    store.update(key=key, update_func=update_func)


def add_user(
    postgres_project_name: str, db_name: str, user: str, password: str
) -> None:
    log.info(
        "Storing info about user %s for database %s (%s)",
        user,
        db_name,
        postgres_project_name,
    )

    def update_func(value: str | None) -> str:
        assert value is not None
        meta = json.loads(value)
        meta["databases"][db_name]["users"][user] = {
            "created": datetime.now(timezone.utc).isoformat(),
            "user": user,
            "password": password,
            "attachments": [],
        }
        new_value = json.dumps(meta)
        return new_value

    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    store.update(key=key, update_func=update_func)


def remove_user(postgres_project_name: str, db_name: str, user: str) -> None:
    log.info(
        "Removing info about user %s for database %s (%s)",
        user,
        db_name,
        postgres_project_name,
    )

    def update_func(value: str | None) -> str:
        assert value is not None
        meta = json.loads(value)
        if user in meta["databases"][db_name]["users"]:
            del meta["databases"][db_name]["users"][user]
        new_value = json.dumps(meta)
        return new_value

    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    store.update(key=key, update_func=update_func)


def add_env_var(
    postgres_project_name: str,
    db_name: str,
    user: str,
    project_name: str,
    var_name: str,
):
    log.info(
        "Saving info about env variable %s for project %s for database %s (%s)",
        var_name,
        project_name,
        db_name,
        postgres_project_name,
    )

    def update_func(value: str | None) -> str:
        assert value is not None
        meta = json.loads(value)
        attachment = {
            "created": datetime.now(timezone.utc).isoformat(),
            "project": project_name,
            "var": var_name,
        }
        meta["databases"][db_name]["users"][user]["attachments"].append(attachment)
        new_value = json.dumps(meta)
        return new_value

    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    store.update(key=key, update_func=update_func)


def get_admin_conn_str(postgres_project_name: str) -> str | None:
    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    value = store.get(key)
    assert value is not None
    meta = json.loads(value)
    if meta["admin"] is None:
        return None
    return misc.conn_string(
        user=meta["admin"]["user"],
        password=meta["admin"]["password"],
        postgres_project_name=postgres_project_name,
        db_name=None,
    )


def get_conn_str(
    postgres_project_name: str,
    db_name: str,
    user: str,
) -> str | None:
    key = POSTGRES_META_KEY.format(project_name=postgres_project_name)
    value = store.get(key)
    assert value is not None
    meta = json.loads(value)
    if db_name not in meta["databases"]:
        return None
    if user not in meta["databases"][db_name]["users"]:
        return None
    password = meta["databases"][db_name]["users"][user]["password"]
    return misc.conn_string(
        user=user,
        password=password,
        postgres_project_name=postgres_project_name,
        db_name=db_name,
    )
