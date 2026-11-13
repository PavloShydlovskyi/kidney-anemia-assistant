"""Інкремент 1: функція нирок.

Revision ID: 0001_kidney
Revises: —
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_kidney"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """TODO (Database Developer):
    - створити patients, lab_results (креатинін, вік, egfr_lab, діаліз), guideline_versions,
      assessments (egfr, gfr_category, measures, guideline_version), reference_thresholds;
    - заповнити guideline_versions і reference_thresholds з infrastructure/reference_seed.py.
    """
    pass


def downgrade() -> None:
    """TODO: скасувати зміни upgrade() у зворотному порядку."""
    pass
