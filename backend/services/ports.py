"""Порти (інтерфейси) доступу до даних і структури для обміну з репозиторіями.

Визначають Backend і Database Developer спільно; реалізації — в infrastructure/.

Інтерфейси:
    ReferenceRepository.get_current() -> ReferenceSet
    AssessmentRepository.save(lab: LabInput, result: AssessmentResult) -> int
    AssessmentRepository.list_by_patient(patient_id: int) -> list[AssessmentRecord]

Структури (dataclass, назви полів = назви колонок БД):
    LabInput         — patient_id, taken_on, age_years, creatinine_umol_l,
                       hemoglobin_g_l, rbc_10e12_l, on_dialysis, egfr_lab
    AssessmentResult — egfr, gfr_category, anemia_grade, rbc_status,
                       measures, guideline_version
    AssessmentRecord — assessment_id, lab, result
    ReferenceSet     — guideline_version, input_limits, gfr_categories,
                       anemia_grades, rbc_reference (доменні Limits, GfrCategory)

Винятки (лише їх обробляє шар API):
    UnknownPatientError — пацієнта немає (API: 404)
    DataIntegrityError  — порушено обмеження БД
    ReferenceDataError  — немає чинної версії або довідник неповний

TODO: інкремент 1 (Backend + Database Developer).
"""
