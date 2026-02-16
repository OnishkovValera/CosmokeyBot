from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a63607a8ecf'
down_revision: Union[str, Sequence[str], None] = '6c302b56ee65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('rewards',
        sa.Column('is_paid', sa.Boolean(), nullable=False, server_default=sa.text('FALSE'))
    )
    op.add_column('rewards',
        sa.Column('processed_at', sa.TIMESTAMP(), nullable=True)
    )

def downgrade():
    op.drop_column('rewards', 'processed_at')
    op.drop_column('rewards', 'is_paid')