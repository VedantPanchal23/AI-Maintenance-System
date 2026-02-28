"""Add missing equipment types to equipmenttype enum

Revision ID: a1b2c3d4e5f6
Revises: e40bf2878c28
Create Date: 2026-02-28 07:40:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e40bf2878c28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New values to add to the 'equipmenttype' PostgreSQL enum
NEW_EQUIPMENT_TYPES = [
    'CNC_MILL',
    'HYDRAULIC_PRESS',
    'INJECTION_MOLDER',
    'CONVEYOR',
    'COMPRESSOR',
    'MOTOR',
]


def upgrade() -> None:
    # PostgreSQL allows adding new values to an existing enum type
    # Each ALTER TYPE must be executed outside a transaction block in some cases,
    # but Alembic runs in transactional mode by default. With PostgreSQL 12+
    # ALTER TYPE ... ADD VALUE IF NOT EXISTS works inside transactions.
    for val in NEW_EQUIPMENT_TYPES:
        op.execute(f"ALTER TYPE equipmenttype ADD VALUE IF NOT EXISTS '{val}'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # To downgrade, you would need to recreate the enum type, which is complex.
    # For safety, we leave this as a no-op.
    pass
