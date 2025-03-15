import logging
import os.path

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


log.info("Disco Postgres addon deploy script")


def main():
    if sqlite_db_exists():
        upgrade()
    else:
        create_sqlite_db()


def upgrade() -> None:
    log.info("Checking if migration step is required")
    from sqlalchemy import text

    import addon
    from addon import keyvalues
    from addon.models.db import Session

    with Session.begin() as dbsession:
        installed_version = keyvalues.get_value(dbsession, key="ADDON_VERSION")
    if installed_version == addon.__version__:
        log.info("Nothing to migrate for now")
        return
    log.info("Upgrading addon")
    if installed_version == "1.0.0":
        log.info("1.0.0 to 1.1.0")
        alembic_upgrade("d49d80339efd")
        with Session.begin() as dbsession:
            dbsession.execute(text("UPDATE instances SET image = 'postgres'"))
        alembic_upgrade("01f55269072f")
        installed_version = "1.1.0"
    if installed_version == "1.1.0":
        log.info("1.1.0 to 1.2.0")
    with Session.begin() as dbsession:
        keyvalues.set_value(dbsession, key="ADDON_VERSION", value=addon.__version__)
    log.info("Done upgrading addon")


def create_sqlite_db() -> None:
    from alembic import command
    from alembic.config import Config

    import addon
    from addon import keyvalues
    from addon.models.db import Session, engine
    from addon.models.meta import base_metadata

    log.info("Creating Postgres addon internal database")
    base_metadata.create_all(engine)
    config = Config("/code/alembic.ini")
    command.stamp(config, "head")
    with Session.begin() as dbsession:
        keyvalues.set_value(dbsession, key="ADDON_VERSION", value=addon.__version__)


def sqlite_db_exists() -> bool:
    return os.path.exists("/addon/data/db.sqlite3")


def alembic_upgrade(version_hash: str) -> None:
    from alembic import command
    from alembic.config import Config

    config = Config("/code/alembic.ini")
    command.upgrade(config, version_hash)


if __name__ == "__main__":
    main()
