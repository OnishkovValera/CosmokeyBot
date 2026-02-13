"""add admin_comment columt to rewards

Revision ID: c9ee6616fdfb
Revises: 69fe47c229e2
Create Date: 2026-02-13 10:55:39.170828

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9ee6616fdfb'
down_revision: Union[str, Sequence[str], None] = '69fe47c229e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('rewards',
        sa.Column('admin_comment', sa.Text(), nullable=True)
    )

def downgrade():
    op.drop_column('rewards', 'admin_comment')