"""create bot tables: users, assistance_requests, messages_texts, rewards"""

from alembic import op
import sqlalchemy as sa

revision = "20260207_create_bot_tables"
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False, unique=True),
        sa.Column('username', sa.String(length=256), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('is_subscribed', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('is_got_reward_for_subscription', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'assistance_requests',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('request_type', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('processed_at', sa.TIMESTAMP(), nullable=True),
    )

    op.create_table(
        'messages_texts',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('message_key', sa.String(length=256), nullable=False, unique=True),
        sa.Column('text', sa.Text(), nullable=False),
    )

    op.create_table(
        'rewards',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('link', sa.String(length=512), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'media_messages',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('assistance_request_id', sa.Integer(), sa.ForeignKey('assistance_requests.id', ondelete='CASCADE'), nullable=True),
        sa.Column('reward_id', sa.Integer(), sa.ForeignKey('rewards.id', ondelete='CASCADE'), nullable=True),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('message_id', sa.BigInteger(), nullable=False),
        sa.Column('media_group_id', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint(
            '(assistance_request_id IS NOT NULL) OR (reward_id IS NOT NULL)',
            name='ck_media_messages_has_owner'
        )
    )

def downgrade():
    op.drop_table('media_messages')
    op.drop_table('rewards')
    op.drop_table('messages_texts')
    op.drop_table('assistance_requests')
    op.drop_table('users')