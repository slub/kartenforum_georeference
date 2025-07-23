#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by tom.schulze@pikobytes.de on 29.04.25.

# This file is subject to the terms and conditions defined in
# file "LICENSE.txt", which is part of this source code package.


"""add external vector maps

Revision ID: 17c30985f013
Revises: a0e44742e445
Create Date: 2025-04-29 15:56:54.003892

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "17c30985f013"
down_revision: Union[str, None] = "a0e44742e445"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


upgrade_sql = """
CREATE TABLE vector_maps_external (
    id SERIAL PRIMARY KEY,
    public_id UUID NOT NULL DEFAULT gen_random_uuid(),

    title TEXT NOT NULL,
    link_content TEXT NOT NULL,
    time_period date[2] NOT NULL,
    description TEXT,
    link_thumb TEXT,
    submitted TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    last_change TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_time_period_shape CHECK (array_ndims(time_period) = 1 AND cardinality(time_period) = 2),
    CONSTRAINT valid_time_period CHECK (time_period[1] <= time_period[2]),

    -- Request tracking
    last_request TIMESTAMP WITHOUT TIME ZONE,
    request_count INTEGER DEFAULT 0
);


CREATE INDEX idx_vector_maps_external_public_id ON vector_maps_external(public_id);
"""

downgrade_sql = """
DROP TABLE vector_maps_external;
DROP INDEX idx_vector_maps_external_public_id;
"""


def upgrade() -> None:
    op.execute(upgrade_sql)


def downgrade() -> None:
    op.execute(downgrade_sql)
