from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59c670b753d2'
down_revision: Union[str, Sequence[str], None] = '846e2ca933c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.create_table(
        'request_comments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('request_type', sa.String(20), nullable=False),  # 'assistance' / 'reward'
        sa.Column('request_id', sa.Integer, nullable=False),
        sa.Column('admin_id', sa.Integer, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('comment', sa.Text, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Index('ix_request_comments_request', 'request_type', 'request_id')
    )

def downgrade():
    op.drop_table('request_comments')