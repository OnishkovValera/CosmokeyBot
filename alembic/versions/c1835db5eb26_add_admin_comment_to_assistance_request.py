from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1835db5eb26'
down_revision: Union[str, Sequence[str], None] = 'a8a0217e38d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('assistance_requests',
        sa.Column('admin_comment', sa.Text(), nullable=True)
    )

def downgrade():
    op.drop_column('assistance_requests', 'admin_comment')