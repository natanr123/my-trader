from sqlmodel import Session, select

import app.core.create_db_engine
from app.core.config.app_settings import app_settings
from app.crud import crud
from app.models.user import User, UserCreate

engine = app.core.create_db_engine.engine


def seed_data(session: Session):
    user = session.exec(
        select(User).where(User.email == app_settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=app_settings.FIRST_SUPERUSER,
            password=app_settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)
    seed_data(session)
