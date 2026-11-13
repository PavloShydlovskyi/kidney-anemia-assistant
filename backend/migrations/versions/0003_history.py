"""Інкремент 3: історія і графіки.

Revision ID: 0003_history
Revises: 0002_anemia
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_history"
down_revision = "0002_anemia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """TODO (Database Developer):
    - індекс ix_lab_results_patient_taken (patient_id, taken_on);
    - за потреби: вид 'measure' і колонка comparison у reference_thresholds.
    """
    pass


def downgrade() -> None:
    """TODO: скасувати зміни upgrade() у зворотному порядку."""
    pass
