"""Add vector_maps

Revision ID: a0e44742e445
Revises:
Create Date: 2024-11-07 14:29:39.527645

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a0e44742e445"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


upgrade_sql = """
CREATE TABLE vector_maps (
    id SERIAL PRIMARY KEY,
    public_id UUID NOT NULL DEFAULT gen_random_uuid(),

    -- Metadata
    description TEXT,
    title TEXT NOT NULL,
    link_thumb TEXT,
    submitted TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    last_change TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),

    -- Request tracking
    last_request TIMESTAMP WITHOUT TIME ZONE,
    request_count INTEGER DEFAULT 0
);


CREATE INDEX idx_vector_maps_public_id ON vector_maps(public_id);

CREATE TABLE vector_maps_content (
    vector_map_id INTEGER NOT NULL REFERENCES vector_maps(id) ON DELETE CASCADE,
    content JSONB NOT NULL,
    version INTEGER NOT NULL,
    created_by TEXT NOT NULL,

    -- metadata
    submitted TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),


    PRIMARY KEY (vector_map_id, version)
);

CREATE INDEX idx_vector_maps_content_id ON vector_maps_content(vector_map_id);

CREATE TYPE vector_map_role AS ENUM ('owner', 'editor');

CREATE TABLE vector_maps_roles (
    vector_map_id INTEGER NOT NULL REFERENCES vector_maps(id) ON DELETE CASCADE,
    role vector_map_role NOT NULL,
    user_id TEXT NOT NULL,

    PRIMARY KEY (vector_map_id, user_id)
);
"""

downgrade_sql = """
DROP INDEX idx_vector_maps_public_id;
DROP INDEX idx_vector_maps_content_id;
DROP TABLE vector_maps_roles;
DROP TABLE vector_maps_content;
DROP TABLE vector_maps;
DROP TYPE vector_map_role;
"""


def upgrade() -> None:
    op.execute(upgrade_sql)


def downgrade() -> None:
    op.execute(downgrade_sql)
