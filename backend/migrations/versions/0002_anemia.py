"""Інкремент 2: оцінка анемії.

Revision ID: 0002_anemia
Revises: 0001_kidney
"""
from alembic import op
import sqlalchemy as sa

from infrastructure.reference_seed import ANEMIA_KINDS, CURRENT_VERSION, reference_rows

# Знімок таблиці на момент міграції — не залежить від майбутніх змін db.py.
_thresholds = sa.table(
    "reference_thresholds",
    sa.column("guideline_version", sa.String), sa.column("kind", sa.String),
    sa.column("parameter", sa.String), sa.column("sex", sa.String),
    sa.column("code", sa.String), sa.column("lower_value", sa.Float),
    sa.column("upper_value", sa.Float), sa.column("unit", sa.String),
)

revision = "0002_anemia"
down_revision = "0001_kidney"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Колонки анемії і рядки довідника anemia_grade, rbc_reference.

    hemoglobin_g_l лишається NULL-допустимою: аналізи інкремента 1 законно не мають Hb,
    а обов'язковість для нових аналізів перевіряє API.
    """
    with op.batch_alter_table("lab_results") as batch:
        batch.add_column(sa.Column("hemoglobin_g_l", sa.Float))
        batch.add_column(sa.Column("rbc_10e12_l", sa.Float))
        batch.create_check_constraint(op.f("ck_lab_results_hemoglobin"), "hemoglobin_g_l > 0")
        batch.create_check_constraint(op.f("ck_lab_results_rbc"), "rbc_10e12_l > 0")
    with op.batch_alter_table("assessments") as batch:
        batch.add_column(sa.Column("anemia_grade", sa.String(8)))
        batch.add_column(sa.Column("rbc_status", sa.String(6)))
        batch.create_check_constraint(op.f("ck_assessments_anemia_grade"),
                                      "anemia_grade IN ('none', 'mild', 'moderate', 'severe')")
        batch.create_check_constraint(op.f("ck_assessments_rbc_status"),
                                      "rbc_status IN ('low', 'normal', 'high')")
    op.bulk_insert(_thresholds, [row for row in reference_rows() if row["kind"] in ANEMIA_KINDS])


def downgrade() -> None:
    """Скасовує зміни upgrade() у зворотному порядку."""
    op.execute(
        _thresholds.delete()
        .where(_thresholds.c.guideline_version == CURRENT_VERSION)
        .where(_thresholds.c.kind.in_(ANEMIA_KINDS))
    )
    with op.batch_alter_table("assessments") as batch:
        batch.drop_constraint(op.f("ck_assessments_rbc_status"), type_="check")
        batch.drop_constraint(op.f("ck_assessments_anemia_grade"), type_="check")
        batch.drop_column("rbc_status")
        batch.drop_column("anemia_grade")
    with op.batch_alter_table("lab_results") as batch:
        batch.drop_constraint(op.f("ck_lab_results_rbc"), type_="check")
        batch.drop_constraint(op.f("ck_lab_results_hemoglobin"), type_="check")
        batch.drop_column("rbc_10e12_l")
        batch.drop_column("hemoglobin_g_l")
