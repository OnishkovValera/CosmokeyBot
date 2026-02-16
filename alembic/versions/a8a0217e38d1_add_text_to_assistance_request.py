from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a8a0217e38d1'
down_revision: Union[str, Sequence[str], None] = '59c670b753d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('assistance_requests',
        sa.Column('text', sa.Text(), nullable=True)
    )
    op.add_column('rewards',
        sa.Column('text', sa.Text(), nullable=True)
    )

def downgrade():
    op.drop_column('assistance_requests', 'text')
    op.drop_column('rewards', 'text')
