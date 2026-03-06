"""add composite index on predictions(equipment_id, timestamp)

Revision ID: b4f5a6c7d8e9
Revises: e40bf2878c28
Create Date: 2026-03-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b4f5a6c7d8e9'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_predictions_equip_time',
        'predictions',
        ['equipment_id', 'timestamp'],
    )


def downgrade() -> None:
    op.drop_index('ix_predictions_equip_time', table_name='predictions')
