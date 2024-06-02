from sqlalchemy.orm import configure_mappers

from addon.models.attachment import Attachment  # noqa: F401
from addon.models.database import Database  # noqa: F401
from addon.models.instance import Instance  # noqa: F401
from addon.models.keyvalue import KeyValue  # noqa: F401
from addon.models.user import User  # noqa: F401

configure_mappers()
