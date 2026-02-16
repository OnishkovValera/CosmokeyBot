from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '846e2ca933c9'
down_revision: Union[str, Sequence[str], None] = '5a63607a8ecf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.add_column('assistance_requests',
        sa.Column('status', sa.String(50), nullable=False, server_default='new')
    )

    op.execute(
        "UPDATE assistance_requests SET status = 'completed' WHERE is_processed = TRUE"
    )

def downgrade():
    op.drop_column('assistance_requests', 'status')