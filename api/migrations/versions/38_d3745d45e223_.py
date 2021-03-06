"""Remove app table

Revision ID: d3745d45e223
Revises: 9569dcac2399
Create Date: 2019-06-21 19:58:34.817643

"""

# revision identifiers, used by Alembic.
revision = "d3745d45e223"
down_revision = "9569dcac2399"

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402
from sqlalchemy.dialects import postgresql  # noqa: E402


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("app")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "app",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("client_name", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column("redirect_uris", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column("scopes", postgresql.ARRAY(sa.VARCHAR(length=255)), autoincrement=False, nullable=False),
        sa.Column("website", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column("client_id", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column("client_secret", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column("inserted_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="app_pkey"),
    )
    # ### end Alembic commands ###
