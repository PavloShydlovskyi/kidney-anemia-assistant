"""Схема БД засобами SQLAlchemy Core і налаштування підключення.

Таблиці: patients, lab_results, assessments, guideline_versions,
reference_thresholds — опис колонок і зв'язків у database/README.md.

Обмеження: PK, FK з ON DELETE RESTRICT, NOT NULL, UNIQUE і CHECK лише для
фізичних інваріантів (значення > 0, дозволені коди). Клінічні граничні
значення в CHECK не дублюються — вони в reference_thresholds.

Індекси: ix_lab_results_patient_taken (patient_id, taken_on),
ix_assessments_lab_result_id, частковий ux_guideline_versions_current.

Для кожного з'єднання SQLite: PRAGMA foreign_keys = ON, journal_mode = WAL,
busy_timeout. Рядок підключення — з налаштувань, не в коді.

TODO: інкремент 1 (Database Developer).
"""
