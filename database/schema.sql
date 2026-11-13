-- Цільова схема БД (SQLite), за звітом Database Developer, п. 2.4.
-- Це довідка: справжня схема описується в backend/infrastructure/db.py
-- і створюється міграціями Alembic (backend/migrations/versions).

CREATE TABLE patients (
    id           INTEGER PRIMARY KEY,
    record_code  VARCHAR(32) NOT NULL UNIQUE,              -- умовний код, без ПІБ
    sex          VARCHAR(6)  NOT NULL CHECK (sex IN ('male', 'female')),
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lab_results (
    id                 INTEGER PRIMARY KEY,
    patient_id         INTEGER NOT NULL REFERENCES patients (id) ON DELETE RESTRICT,
    taken_on           DATE    NOT NULL,
    age_years          INTEGER NOT NULL CHECK (age_years BETWEEN 0 AND 130),
    creatinine_umol_l  FLOAT   NOT NULL CHECK (creatinine_umol_l > 0),
    hemoglobin_g_l     FLOAT   CHECK (hemoglobin_g_l > 0),
    rbc_10e12_l        FLOAT   CHECK (rbc_10e12_l > 0),
    egfr_lab           FLOAT   CHECK (egfr_lab >= 0),       -- ШКФ від лабораторії
    on_dialysis        BOOLEAN NOT NULL DEFAULT 0
);
CREATE INDEX ix_lab_results_patient_taken ON lab_results (patient_id, taken_on);

CREATE TABLE guideline_versions (
    version     VARCHAR(40)  PRIMARY KEY,                   -- 'KDIGO-2024/WHO-2024'
    title       VARCHAR(200) NOT NULL,
    is_current  BOOLEAN      NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX ux_guideline_versions_current
    ON guideline_versions (is_current) WHERE is_current = 1;

CREATE TABLE assessments (
    id                 INTEGER PRIMARY KEY,
    lab_result_id      INTEGER NOT NULL REFERENCES lab_results (id) ON DELETE RESTRICT,
    egfr               FLOAT   NOT NULL CHECK (egfr >= 0),  -- без верхньої межі
    gfr_category       VARCHAR(3) NOT NULL
                       CHECK (gfr_category IN ('G1', 'G2', 'G3a', 'G3b', 'G4', 'G5')),
    anemia_grade       VARCHAR(8) CHECK (anemia_grade IN ('none', 'mild', 'moderate', 'severe')),
    rbc_status         VARCHAR(6) CHECK (rbc_status IN ('low', 'normal', 'high')),
    measures           JSON    NOT NULL,                    -- знімок заходів для розгляду
    guideline_version  VARCHAR(40) NOT NULL REFERENCES guideline_versions (version),
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_assessments_lab_result_id ON assessments (lab_result_id);

CREATE TABLE reference_thresholds (
    id                 INTEGER PRIMARY KEY,
    guideline_version  VARCHAR(40) NOT NULL REFERENCES guideline_versions (version),
    kind               VARCHAR(16) NOT NULL
                       CHECK (kind IN ('input_limit', 'gfr_category', 'anemia_grade', 'rbc_reference')),
    parameter          VARCHAR(16) NOT NULL,                -- egfr, creatinine, hemoglobin, rbc
    sex                VARCHAR(6)  NOT NULL DEFAULT 'any' CHECK (sex IN ('male', 'female', 'any')),
    code               VARCHAR(8)  NOT NULL DEFAULT '',     -- G3a, mild, normal
    lower_value        FLOAT,
    upper_value        FLOAT,
    unit               VARCHAR(16) NOT NULL,                -- umol_l, g_l, 10e12_l, ml_min_1_73m2
    UNIQUE (guideline_version, kind, parameter, sex, code),
    CHECK (lower_value IS NOT NULL OR upper_value IS NOT NULL),
    CHECK (lower_value <= upper_value)
);
