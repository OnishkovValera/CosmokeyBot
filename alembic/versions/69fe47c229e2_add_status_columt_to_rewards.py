"""add status columt to rewards

Revision ID: 69fe47c229e2
Revises: 0f2eeb21433c
Create Date: 2026-02-13 10:52:07.091753

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69fe47c229e2'
down_revision: Union[str, Sequence[str], None] = '0f2eeb21433c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('rewards',
        sa.Column('status', sa.String(50), nullable=False, server_default='new')
    )
    # Синхронизируем статус с is_paid
    op.execute("UPDATE rewards SET status = 'completed' WHERE is_paid = TRUE")
    op.execute("UPDATE rewards SET status = 'new' WHERE status IS NULL")

def downgrade():
    op.drop_column('rewards', 'status')