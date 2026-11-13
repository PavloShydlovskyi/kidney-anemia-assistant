"""Реалізації портів на SQLAlchemy.

SqlAlchemyReferenceRepository.get_current()
    SELECT чинної версії з guideline_versions, потім її рядків із
    reference_thresholds; перетворення рядків на доменні Limits і GfrCategory.
    Для API: input_limit з parameter = 'egfr' віддається як indicator 'egfr_lab'.

SqlAlchemyAssessmentRepository.save(lab, result)
    Одна транзакція: перевірка пацієнта, INSERT у lab_results,
    INSERT в assessments; у разі помилки відкочуються обидва записи.

SqlAlchemyAssessmentRepository.list_by_patient(patient_id)
    Один SELECT із JOIN lab_results і assessments, ORDER BY taken_on.

Правила: лише параметризовані запити, явні колонки, без клінічної логіки;
винятки SQLAlchemy перетворюються на винятки з services/ports.py.

TODO: інкремент 1 (Database Developer).
"""
