"""initial_schema

Revision ID: 6326402750e5
Revises: 01_initial_tables
Create Date: 2025-05-12 21:09:56.418030

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6326402750e5'
down_revision: Union[str, None] = '01_initial_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass