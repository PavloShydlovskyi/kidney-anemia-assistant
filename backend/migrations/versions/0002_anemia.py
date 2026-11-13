"""Інкремент 2: оцінка анемії.

Revision ID: 0002_anemia
Revises: 0001_kidney
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_anemia"
down_revision = "0001_kidney"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """TODO (Database Developer):
    - lab_results: hemoglobin_g_l, rbc_10e12_l;
    - assessments: anemia_grade, rbc_status;
    - reference_thresholds: рядки anemia_grade і rbc_reference.
    """
    pass


def downgrade() -> None:
    """TODO: скасувати зміни upgrade() у зворотному порядку."""
    pass
