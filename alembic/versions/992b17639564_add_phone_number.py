from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '992b17639564'
down_revision: Union[str, Sequence[str], None] = 'b10d9c1e191c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.add_column('users',
        sa.Column('phone_number', sa.String(length=20), nullable=True)
    )

def downgrade():
    op.drop_column('users', 'phone_number')