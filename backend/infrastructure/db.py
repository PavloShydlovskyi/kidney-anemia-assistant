"""Схема БД (SQLAlchemy Core) і підключення до SQLite.

Відповідальний: Database Developer. Опис таблиць — database/README.md,
згенерований SQL для довідки — database/schema.sql.

Правила:
- CHECK лише для фізичних інваріантів (значення > 0, дозволені коди);
  клінічні межі зберігаються в reference_thresholds, а не в CHECK;
- для кожного з'єднання SQLite: foreign_keys = ON, journal_mode = WAL, busy_timeout;
- без специфічного SQL, щоб схема працювала і на PostgreSQL.
"""
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Engine,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
)

DEFAULT_DATABASE_URL = "sqlite:///kidney.db"
SQLITE_BUSY_TIMEOUT_MS = 5000

# Однакові імена обмежень у SQLite і PostgreSQL (потрібно для міграцій Alembic).
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=NAMING_CONVENTION)


# ---------- Таблиці ----------
# Ключові колонки вже є, щоб на таблиці можна було посилатися.
# TODO (Database Developer): решта колонок, CHECK, UNIQUE та індекси — за звітом, п. 2.4.

patients = Table(
    "patients", metadata,
    Column("id", Integer, primary_key=True),
    # TODO: record_code String(32) NOT NULL UNIQUE — умовний код, без ПІБ
    # TODO: sex String(6) NOT NULL, CHECK sex IN ('male', 'female')
    # TODO: created_at DateTime NOT NULL, server_default CURRENT_TIMESTAMP
)

lab_results = Table(
    "lab_results", metadata,
    Column("id", Integer, primary_key=True),
    Column("patient_id", Integer, ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
    Column("taken_on", Date, nullable=False),
    # TODO: age_years Integer NOT NULL, CHECK 0..130
    # TODO: creatinine_umol_l Float NOT NULL, CHECK > 0
    # TODO: hemoglobin_g_l Float, CHECK > 0
    # TODO: rbc_10e12_l Float, CHECK > 0
    # TODO: egfr_lab Float, CHECK >= 0
    # TODO: on_dialysis Boolean NOT NULL DEFAULT false
    # TODO: індекс ix_lab_results_patient_taken (patient_id, taken_on)
)

guideline_versions = Table(
    "guideline_versions", metadata,
    Column("version", String(40), primary_key=True),
    # TODO: title String(200) NOT NULL
    # TODO: is_current Boolean NOT NULL DEFAULT false
    # TODO: частковий унікальний індекс ux_guideline_versions_current WHERE is_current
)

assessments = Table(
    "assessments", metadata,
    Column("id", Integer, primary_key=True),
    Column("lab_result_id", Integer, ForeignKey("lab_results.id", ondelete="RESTRICT"), nullable=False),
    Column("guideline_version", String(40), ForeignKey("guideline_versions.version"), nullable=False),
    # TODO: egfr Float NOT NULL, CHECK >= 0 (без верхньої межі)
    # TODO: gfr_category String(3) NOT NULL, CHECK IN ('G1','G2','G3a','G3b','G4','G5')
    # TODO: anemia_grade String(8), CHECK IN ('none','mild','moderate','severe')
    # TODO: rbc_status String(6), CHECK IN ('low','normal','high')
    # TODO: measures JSON NOT NULL
    # TODO: created_at DateTime NOT NULL, server_default CURRENT_TIMESTAMP
    # TODO: індекс ix_assessments_lab_result_id
)

reference_thresholds = Table(
    "reference_thresholds", metadata,
    Column("id", Integer, primary_key=True),
    Column("guideline_version", String(40), ForeignKey("guideline_versions.version"), nullable=False),
    # TODO: kind String(16) NOT NULL, CHECK IN ('input_limit','gfr_category','anemia_grade','rbc_reference')
    # TODO: parameter String(16) NOT NULL — egfr, creatinine, hemoglobin, rbc
    # TODO: sex String(6) NOT NULL DEFAULT 'any', CHECK IN ('male','female','any')
    # TODO: code String(8) NOT NULL DEFAULT '' — G3a, mild, normal
    # TODO: lower_value Float, upper_value Float, unit String(16) NOT NULL
    # TODO: UNIQUE (guideline_version, kind, parameter, sex, code)
    # TODO: CHECK (lower_value IS NOT NULL OR upper_value IS NOT NULL), CHECK (lower_value <= upper_value)
)


# ---------- Підключення ----------

def create_db_engine(url: str = DEFAULT_DATABASE_URL) -> Engine:
    """Створює рушій і для SQLite вмикає PRAGMA на кожному з'єднанні.

    TODO (Database Developer): create_engine(url) + event.listen(engine, "connect",
    _apply_sqlite_pragmas), якщо url починається з "sqlite".
    """
    raise NotImplementedError


def _apply_sqlite_pragmas(dbapi_connection, connection_record) -> None:
    """TODO: PRAGMA foreign_keys = ON; journal_mode = WAL; busy_timeout = SQLITE_BUSY_TIMEOUT_MS."""
    raise NotImplementedError


def create_schema(engine: Engine) -> None:
    """Створює всі таблиці (для тестів). У роботі схему створюють міграції Alembic."""
    metadata.create_all(engine)
