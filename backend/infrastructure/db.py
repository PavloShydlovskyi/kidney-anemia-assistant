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
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Engine,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    event,
    false,
    func,
    text,
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
# Кінцевий стан після всіх міграцій; tests/test_migrations.py перевіряє,
# що migrations/versions дають саме цю схему.

patients = Table(
    "patients", metadata,
    Column("id", Integer, primary_key=True),
    Column("record_code", String(32), nullable=False, unique=True),   # умовний код, без ПІБ
    Column("sex", String(6), nullable=False),
    Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    CheckConstraint("sex IN ('male', 'female')", name="sex"),
)

lab_results = Table(
    "lab_results", metadata,
    Column("id", Integer, primary_key=True),
    Column("patient_id", Integer, ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
    Column("taken_on", Date, nullable=False),
    Column("age_years", Integer, nullable=False),              # вік на дату аналізу
    Column("creatinine_umol_l", Float, nullable=False),
    Column("hemoglobin_g_l", Float),                           # NULL — аналізи інкремента 1
    Column("rbc_10e12_l", Float),
    Column("egfr_lab", Float),                                 # ШКФ від лабораторії, якщо є
    Column("on_dialysis", Boolean, nullable=False, server_default=false()),
    CheckConstraint("age_years BETWEEN 0 AND 130", name="age"),
    CheckConstraint("creatinine_umol_l > 0", name="creatinine"),
    CheckConstraint("hemoglobin_g_l > 0", name="hemoglobin"),
    CheckConstraint("rbc_10e12_l > 0", name="rbc"),
    CheckConstraint("egfr_lab >= 0", name="egfr_lab"),
    Index("ix_lab_results_patient_taken", "patient_id", "taken_on"),
)

guideline_versions = Table(
    "guideline_versions", metadata,
    Column("version", String(40), primary_key=True),           # 'KDIGO-2024/WHO-2024'
    Column("title", String(200), nullable=False),
    Column("is_current", Boolean, nullable=False, server_default=false()),
    # Чинною може бути лише одна версія настанов
    Index("ux_guideline_versions_current", "is_current", unique=True,
          sqlite_where=text("is_current = 1"), postgresql_where=text("is_current")),
)

assessments = Table(
    "assessments", metadata,
    Column("id", Integer, primary_key=True),
    Column("lab_result_id", Integer, ForeignKey("lab_results.id", ondelete="RESTRICT"), nullable=False),
    Column("guideline_version", String(40), ForeignKey("guideline_versions.version"), nullable=False),
    Column("egfr", Float, nullable=False),                     # без верхньої межі: може бути > 100
    Column("gfr_category", String(3), nullable=False),
    Column("anemia_grade", String(8)),
    Column("rbc_status", String(6)),
    Column("measures", JSON, nullable=False),                  # знімок заходів для розгляду
    Column("created_at", DateTime, nullable=False, server_default=func.current_timestamp()),
    CheckConstraint("egfr >= 0", name="egfr"),
    CheckConstraint("gfr_category IN ('G1', 'G2', 'G3a', 'G3b', 'G4', 'G5')", name="gfr_category"),
    CheckConstraint("anemia_grade IN ('none', 'mild', 'moderate', 'severe')", name="anemia_grade"),
    CheckConstraint("rbc_status IN ('low', 'normal', 'high')", name="rbc_status"),
    Index("ix_assessments_lab_result_id", "lab_result_id"),
)

reference_thresholds = Table(
    "reference_thresholds", metadata,
    Column("id", Integer, primary_key=True),
    Column("guideline_version", String(40), ForeignKey("guideline_versions.version"), nullable=False),
    Column("kind", String(16), nullable=False),
    Column("parameter", String(16), nullable=False),           # egfr, creatinine, hemoglobin, rbc
    Column("sex", String(6), nullable=False, server_default="any"),
    Column("code", String(8), nullable=False, server_default=""),   # G3a, mild, normal
    Column("lower_value", Float),
    Column("upper_value", Float),
    Column("unit", String(16), nullable=False),                # umol_l, g_l, 10e12_l, ml_min_1_73m2
    UniqueConstraint("guideline_version", "kind", "parameter", "sex", "code",
                     name="uq_reference_thresholds_row"),
    CheckConstraint("kind IN ('input_limit', 'gfr_category', 'anemia_grade', 'rbc_reference')",
                    name="kind"),
    CheckConstraint("sex IN ('male', 'female', 'any')", name="sex"),
    CheckConstraint("lower_value IS NOT NULL OR upper_value IS NOT NULL", name="has_bound"),
    CheckConstraint("lower_value <= upper_value", name="bounds_order"),
)


# ---------- Підключення ----------

def create_db_engine(url: str = DEFAULT_DATABASE_URL) -> Engine:
    """Створює рушій і для SQLite вмикає PRAGMA на кожному з'єднанні."""
    engine = create_engine(url)
    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _apply_sqlite_pragmas)
    return engine


def _apply_sqlite_pragmas(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")      # за замовчуванням SQLite не перевіряє FK
    cursor.execute("PRAGMA journal_mode = WAL")     # читання не блокується записом
    cursor.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    cursor.close()


def create_schema(engine: Engine) -> None:
    """Створює всі таблиці (для тестів). У роботі схему створюють міграції Alembic."""
    metadata.create_all(engine)
