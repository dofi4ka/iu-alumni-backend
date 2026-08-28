"""Drop cities table (city lookup moved to embedded dataset)

Revision ID: h1i2j3k4l5
Revises: b8cc16a01785, d7e8f9a0b1c2
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'h1i2j3k4l5'
down_revision: Union[str, None] = ('b8cc16a01785', 'd7e8f9a0b1c2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Dropping the table also drops its indexes (idx_city_name, idx_country,
    # ix_cities_city_trgm).
    op.drop_table('cities')


def downgrade() -> None:
    # The City model was removed and the data now lives in app/data/cities.tsv;
    # there is nothing to restore here.
    pass
