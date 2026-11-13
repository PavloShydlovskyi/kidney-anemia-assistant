"""Інкремент 1: функція нирок.

Revision ID: 0001_kidney
Revises: —
"""
from alembic import op
import sqlalchemy as sa

from infrastructure.reference_seed import KIDNEY_KINDS, guideline_version_row, reference_rows

revision = "0001_kidney"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Таблиці інкремента 1 і довідник (граничні значення, категорії G1–G5)."""
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("record_code", sa.String(32), nullable=False),
        sa.Column("sex", sa.String(6), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_patients")),
        sa.UniqueConstraint("record_code", name=op.f("uq_patients_record_code")),
        sa.CheckConstraint("sex IN ('male', 'female')", name=op.f("ck_patients_sex")),
    )
    op.create_table(
        "lab_results",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("patient_id", sa.Integer, nullable=False),
        sa.Column("taken_on", sa.Date, nullable=False),
        sa.Column("age_years", sa.Integer, nullable=False),
        sa.Column("creatinine_umol_l", sa.Float, nullable=False),
        sa.Column("egfr_lab", sa.Float),
        sa.Column("on_dialysis", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lab_results")),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="RESTRICT",
                                name=op.f("fk_lab_results_patient_id_patients")),
        sa.CheckConstraint("age_years BETWEEN 0 AND 130", name=op.f("ck_lab_results_age")),
        sa.CheckConstraint("creatinine_umol_l > 0", name=op.f("ck_lab_results_creatinine")),
        sa.CheckConstraint("egfr_lab >= 0", name=op.f("ck_lab_results_egfr_lab")),
    )
    versions = op.create_table(
        "guideline_versions",
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("version", name=op.f("pk_guideline_versions")),
    )
    op.create_index("ux_guideline_versions_current", "guideline_versions", ["is_current"],
                    unique=True, sqlite_where=sa.text("is_current = 1"),
                    postgresql_where=sa.text("is_current"))
    op.create_table(
        "assessments",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("lab_result_id", sa.Integer, nullable=False),
        sa.Column("guideline_version", sa.String(40), nullable=False),
        sa.Column("egfr", sa.Float, nullable=False),
        sa.Column("gfr_category", sa.String(3), nullable=False),
        sa.Column("measures", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessments")),
        sa.ForeignKeyConstraint(["lab_result_id"], ["lab_results.id"], ondelete="RESTRICT",
                                name=op.f("fk_assessments_lab_result_id_lab_results")),
        sa.ForeignKeyConstraint(["guideline_version"], ["guideline_versions.version"],
                                name=op.f("fk_assessments_guideline_version_guideline_versions")),
        sa.CheckConstraint("egfr >= 0", name=op.f("ck_assessments_egfr")),
        sa.CheckConstraint("gfr_category IN ('G1', 'G2', 'G3a', 'G3b', 'G4', 'G5')",
                           name=op.f("ck_assessments_gfr_category")),
    )
    op.create_index("ix_assessments_lab_result_id", "assessments", ["lab_result_id"])
    thresholds = op.create_table(
        "reference_thresholds",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("guideline_version", sa.String(40), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("parameter", sa.String(16), nullable=False),
        sa.Column("sex", sa.String(6), nullable=False, server_default="any"),
        sa.Column("code", sa.String(8), nullable=False, server_default=""),
        sa.Column("lower_value", sa.Float),
        sa.Column("upper_value", sa.Float),
        sa.Column("unit", sa.String(16), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reference_thresholds")),
        sa.ForeignKeyConstraint(["guideline_version"], ["guideline_versions.version"],
                                name=op.f("fk_reference_thresholds_guideline_version_guideline_versions")),
        sa.UniqueConstraint("guideline_version", "kind", "parameter", "sex", "code",
                            name=op.f("uq_reference_thresholds_row")),
        sa.CheckConstraint("kind IN ('input_limit', 'gfr_category', 'anemia_grade', 'rbc_reference')",
                           name=op.f("ck_reference_thresholds_kind")),
        sa.CheckConstraint("sex IN ('male', 'female', 'any')", name=op.f("ck_reference_thresholds_sex")),
        sa.CheckConstraint("lower_value IS NOT NULL OR upper_value IS NOT NULL",
                           name=op.f("ck_reference_thresholds_has_bound")),
        sa.CheckConstraint("lower_value <= upper_value", name=op.f("ck_reference_thresholds_bounds_order")),
    )
    op.bulk_insert(versions, [guideline_version_row()])
    op.bulk_insert(thresholds, [row for row in reference_rows() if row["kind"] in KIDNEY_KINDS])


def downgrade() -> None:
    """Скасовує зміни upgrade() у зворотному порядку."""
    op.drop_table("reference_thresholds")
    op.drop_index("ix_assessments_lab_result_id", table_name="assessments")
    op.drop_table("assessments")
    op.drop_index("ux_guideline_versions_current", table_name="guideline_versions")
    op.drop_table("guideline_versions")
    op.drop_table("lab_results")
    op.drop_table("patients")
