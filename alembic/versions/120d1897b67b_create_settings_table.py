from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '120d1897b67b'
down_revision: Union[str, Sequence[str], None] = 'c9ee6616fdfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'settings',
        sa.Column('key', sa.String(255), primary_key=True),
        sa.Column('value', sa.Text, nullable=False),
    )
    op.execute("""
        INSERT INTO settings (key, value) VALUES 
        ('info_chat_id', '0'),
        ('info_message_id', '0')
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """)

def downgrade():
    op.drop_table('settings')