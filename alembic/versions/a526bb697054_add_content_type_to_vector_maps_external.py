"""add content_type to vector_maps_external

Revision ID: a526bb697054
Revises: 35ee03548b28
Create Date: 2025-05-19 15:42:17.652345

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a526bb697054"
down_revision: Union[str, None] = "35ee03548b28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


upgrade_sql = """
ALTER TABLE IF EXISTS vector_maps_external ADD COLUMN IF NOT EXISTS content_type TEXT NOT NULL DEFAULT 'vkf:geojson-spec-v1';
"""

downgrade_sql = """
ALTER TABLE IF EXISTS vector_maps DROP COLUMN IF EXISTS content_type;
"""


def upgrade() -> None:
    op.execute(upgrade_sql)


def downgrade() -> None:
    op.execute(downgrade_sql)
