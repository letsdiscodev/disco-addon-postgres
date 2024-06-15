import logging
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm.session import Session as DBSession

from addon import misc
from addon.models import Attachment, Database, Instance, User
from addon.models.db import Session

log = logging.getLogger(__name__)


def add_postgres_instance(
    instance_name: str, version: str, admin_user: str, admin_password: str
) -> None:
    log.info("Saving info about new instance %s", instance_name)
    with Session.begin() as dbsession:
        instance = Instance(
            name=instance_name,
            version=version,
            admin_user=admin_user,
            admin_password=admin_password,
        )
        dbsession.add(instance)


def remove_postgres_instance(instance_name: str) -> None:
    log.info("Removing info about instance %s", instance_name)
    with Session.begin() as dbsession:
        instance = get_instance_by_name(dbsession, instance_name)
        if instance is None:
            log.info("Instance not found, doing nothing")
            return
        for database in instance.databases:
            dbsession.delete(database)
        dbsession.delete(instance)


def add_db(
    instance_name: str,
    db_name: str,
) -> None:
    log.info("Storing info about database %s (%s)", db_name, instance_name)
    with Session.begin() as dbsession:
        instance = get_instance_by_name(
            dbsession=dbsession, instance_name=instance_name
        )
        assert instance is not None
        database = Database(
            name=db_name,
            instance=instance,
        )
        dbsession.add(database)


def remove_db(
    instance_name: str,
    db_name: str,
) -> None:
    log.info("Removing info about database %s (%s)", db_name, instance_name)
    with Session.begin() as dbsession:
        database = get_database(
            dbsession=dbsession, instance_name=instance_name, db_name=db_name
        )
        if database is None:
            log.info("Database not found, doing nothing")
            return
        assert len(database.users) == 0
        dbsession.delete(database)


def add_user(instance_name: str, db_name: str, user_name: str, password: str) -> None:
    log.info(
        "Storing info about user %s for database %s (%s)",
        user_name,
        db_name,
        instance_name,
    )

    with Session.begin() as dbsession:
        database = get_database(
            dbsession=dbsession, instance_name=instance_name, db_name=db_name
        )
        assert database is not None
        user = User(
            name=user_name,
            password=password,
            database=database,
        )
        dbsession.add(user)


def get_database(
    dbsession: DBSession, instance_name: str, db_name: str
) -> Database | None:
    stmt = (
        select(Database)
        .join(Instance)
        .where(Database.name == db_name)
        .where(Instance.name == instance_name)
        .limit(1)
    )
    result = dbsession.execute(stmt)
    database = result.scalars().first()
    return database


def remove_user(instance_name: str, db_name: str, user_name: str) -> None:
    log.info(
        "Removing info about user %s for database %s (%s)",
        user_name,
        db_name,
        instance_name,
    )
    with Session.begin() as dbsession:
        user = get_user(
            dbsession=dbsession,
            instance_name=instance_name,
            db_name=db_name,
            user_name=user_name,
        )
        if user is None:
            log.info("User not found, doing nothing")
            return
        for attachment in user.attachments:
            dbsession.delete(attachment)
        dbsession.delete(user)


def add_attachment(
    instance_name: str,
    db_name: str,
    user_name: str,
    project_name: str,
    var_name: str,
):
    log.info(
        "Saving info about env variable %s for project %s for database %s (%s)",
        var_name,
        project_name,
        db_name,
        instance_name,
    )
    with Session.begin() as dbsession:
        user = get_user(
            dbsession=dbsession,
            instance_name=instance_name,
            db_name=db_name,
            user_name=user_name,
        )
        assert user is not None
        attachment = Attachment(
            project_name=project_name,
            env_var=var_name,
            user=user,
        )
        dbsession.add(attachment)


def get_user(
    dbsession: DBSession, instance_name: str, db_name: str, user_name: str
) -> User | None:
    stmt = (
        select(User)
        .join(Database)
        .join(Instance)
        .where(User.name == user_name)
        .where(Database.name == db_name)
        .where(Instance.name == instance_name)
        .limit(1)
    )
    result = dbsession.execute(stmt)
    user = result.scalars().first()
    return user


def get_admin_conn_str(instance_name: str) -> str | None:
    with Session.begin() as dbsession:
        instance = get_instance_by_name(dbsession, instance_name)
        assert instance is not None
        return misc.conn_string(
            user=instance.admin_user,
            password=instance.admin_password,
            postgres_project_name=misc.instance_project_name(instance_name),
            db_name=None,
        )


def get_instance_by_name(dbsession, instance_name) -> Instance | None:
    stmt = select(Instance).where(Instance.name == instance_name).limit(1)
    result = dbsession.execute(stmt)
    instance = result.scalars().first()
    return instance


def get_attachments_for_instance(
    dbsession: DBSession, instance: Instance
) -> Sequence[Attachment]:
    stmt = (
        select(Attachment)
        .join(User)
        .join(Database)
        .where(Database.instance == instance)
    )
    result = dbsession.execute(stmt)
    attachments = result.scalars().all()
    return attachments


def get_attachments(
    dbsession: DBSession,
    instance_name: str,
    db_name: str,
    project_name: str,
    env_var: str | None,
) -> Sequence[Attachment]:
    stmt = (
        select(Attachment)
        .join(User)
        .join(Database)
        .where(Attachment.project_name == project_name)
        .where(Database.name == db_name)
        .where(Instance.name == instance_name)
    )
    if env_var is not None:
        stmt = stmt.where(Attachment.env_var == env_var)
    result = dbsession.execute(stmt)
    attachments = result.scalars().all()
    return attachments


def get_instances(dbsession: DBSession) -> Sequence[Instance]:
    stmt = select(Instance)
    result = dbsession.execute(stmt)
    attachments = result.scalars().all()
    return attachments


def get_attachments_for_project(
    dbsession: DBSession,
    project_name: str,
    env_var: str | None,
) -> Sequence[Attachment]:
    stmt = select(Attachment).where(Attachment.project_name == project_name)
    if env_var is not None:
        stmt = stmt.where(Attachment.env_var == env_var)
    result = dbsession.execute(stmt)
    attachments = result.scalars().all()
    return attachments
