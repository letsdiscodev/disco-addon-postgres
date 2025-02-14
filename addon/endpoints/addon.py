from fastapi import APIRouter

from addon import keyvalues, storage
from addon.models.db import Session

router = APIRouter()


@router.get("/addon")
def addon_get():
    with Session.begin() as dbsession:
        instances = storage.get_instances(dbsession)
        return {
            "addon": {
                "version": keyvalues.get_value(dbsession, key="ADDON_VERSION"),
            },
            "instances": [
                {
                    "created": instance.created.isoformat(),
                    "name": instance.name,
                    "image": instance.image,
                    "version": instance.version,
                    "databases": [
                        {
                            "created": database.created.isoformat(),
                            "name": database.name,
                            "users": [
                                {
                                    "created": user.created.isoformat(),
                                    "name": user.name,
                                    "attachments": [
                                        {
                                            "created": attachment.created.isoformat(),
                                            "project": attachment.project_name,
                                            "envVar": attachment.env_var,
                                        }
                                        for attachment in user.attachments
                                    ],
                                }
                                for user in database.users
                            ],
                        }
                        for database in instance.databases
                    ],
                }
                for instance in instances
            ],
        }
