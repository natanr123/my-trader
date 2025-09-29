"""add_sell_failed_status

Revision ID: a7ee2c7ab1f2
Revises: 5c787d49cc37
Create Date: 2025-09-30 02:08:31.148085

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'a7ee2c7ab1f2'
down_revision = '5c787d49cc37'
branch_labels = None
depends_on = None


def upgrade():
    # Add SELL_FAILED to the virtualorderstatus enum
    op.execute("ALTER TYPE virtualorderstatus ADD VALUE 'SELL_FAILED'")


def downgrade():
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum and updating all references
    pass
