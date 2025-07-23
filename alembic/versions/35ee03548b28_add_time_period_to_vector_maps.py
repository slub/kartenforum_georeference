"""add time period to vector maps

Revision ID: 35ee03548b28
Revises: 17c30985f013
Create Date: 2025-05-14 17:22:52.717802

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "35ee03548b28"
down_revision: Union[str, None] = "17c30985f013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


upgrade_sql = """
BEGIN TRANSACTION;
    ALTER TABLE IF EXISTS vector_maps
        ADD COLUMN IF NOT EXISTS time_period date[2];

    -- set time_period default to the submitted date
    -- this also reflects the current behavior in the client
    UPDATE vector_maps target
        SET time_period = ARRAY[source.submitted, source.submitted]
        FROM vector_maps source
        WHERE target.id = source.id;

    ALTER TABLE IF EXISTS vector_maps ALTER COLUMN time_period SET NOT NULL;

    ALTER TABLE IF EXISTS vector_maps
        ADD CONSTRAINT valid_time_period_shape CHECK (array_ndims(time_period) = 1 AND cardinality(time_period) = 2),
        ADD CONSTRAINT valid_time_period CHECK (time_period[1] <= time_period[2]);
COMMIT;
"""

downgrade_sql = """
ALTER TABLE IF EXISTS vector_maps DROP COLUMN IF EXISTS time_period;
"""


def upgrade() -> None:
    op.execute(upgrade_sql)


def downgrade() -> None:
    op.execute(downgrade_sql)
