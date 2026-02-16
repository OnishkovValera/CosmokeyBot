from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6c302b56ee65'
down_revision: Union[str, Sequence[str], None] = '992b17639564'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column('rewards', 'link',
                    existing_type=sa.String(length=512),
                    nullable=True)


def downgrade():
    op.alter_column('rewards', 'link',
                    existing_type=sa.String(length=512),
                    nullable=False)
