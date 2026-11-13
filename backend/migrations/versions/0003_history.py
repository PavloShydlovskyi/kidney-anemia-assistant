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
    """Індекс для запиту історії пацієнта (WHERE patient_id ORDER BY taken_on).

    Вид 'measure' і колонку comparison додасть окрема міграція, коли пороги заходів
    перейдуть із domain/measures.py у довідник.
    """
    op.create_index("ix_lab_results_patient_taken", "lab_results", ["patient_id", "taken_on"])


def downgrade() -> None:
    """Скасовує зміни upgrade()."""
    op.drop_index("ix_lab_results_patient_taken", table_name="lab_results")
