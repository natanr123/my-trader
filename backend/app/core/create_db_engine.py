# This file is created (Instead just place create_engine in db.py) in order to make the importing of models (before create_engine) explicit
from sqlmodel import create_engine

import app.models.item

# Importing models before create_engine
import app.models.order
import app.models.user
from app.core.config.db_settings import settings as db_settings

Order = app.models.order.Order
Item = app.models.item.Item
User = app.models.user.User

##############################################

# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28

engine = create_engine(str(db_settings.SQLALCHEMY_DATABASE_URI))


__all__ = ['engine']