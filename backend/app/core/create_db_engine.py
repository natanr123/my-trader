# This file is created (Instead just place create_engine in db.py) in order to make the importing of models (before create_engine) explicit
from sqlmodel import create_engine
from app.core.config import settings

# Importing models before create_engine

import app.models.order, app.models.item, app.models.user
Order = app.models.order.Order
Item = app.models.item.Item
User = app.models.user.User

##############################################

# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))