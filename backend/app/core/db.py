from sqlmodel import Session, select

import app.core.create_db_engine
from app.core.config.app_settings import app_settings
from app.crud import crud
from app.models.user import User, UserCreate
from app.core.config.super_user_settings import super_user_settings

engine = app.core.create_db_engine.engine


def seed_data(session: Session):
    user = session.exec(
        select(User).where(User.email == super_user_settings.FIRST_SUPER_USER_USERNAME)
    ).first()
    if not user:
        user_in = UserCreate(
            email=super_user_settings.FIRST_SUPER_USER_USERNAME,
            password=app_settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)
    else:
        # Update existing user to ensure correct credentials
        user.email = app_settings.FIRST_SUPERUSER
        user.hashed_password = crud.get_password_hash(app_settings.FIRST_SUPERUSER_PASSWORD)
        user.is_superuser = True
        session.add(user)
        session.commit()
        session.refresh(user)


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)
    seed_data(session)
