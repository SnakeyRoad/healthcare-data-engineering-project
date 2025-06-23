-- Healthcare Data Engineering Project - Required Queries
-- Five cross-dataset queries meeting project requirements

-- Query 1: Average age and age range of patients (REQUIRED)
-- Uses: patients table
SELECT 
    ROUND(AVG(EXTRACT(YEAR FROM AGE(date_of_birth))), 2) AS average_age,
    MIN(EXTRACT(YEAR FROM AGE(date_of_birth))) AS min_age,
    MAX(EXTRACT(YEAR FROM AGE(date_of_birth))) AS max_age,
    MAX(EXTRACT(YEAR FROM AGE(date_of_birth))) - MIN(EXTRACT(YEAR FROM AGE(date_of_birth))) AS age_range,
    COUNT(*) AS total_patients
FROM patients
WHERE date_of_birth IS NOT NULL;

-- Query 2: Average patients per physician (REQUIRED)
-- Uses: encounters table (provider_id represents physicians)
SELECT 
    ROUND(AVG(patient_count), 2) AS avg_patients_per_physician,
    COUNT(provider_id) AS total_physicians,
    SUM(patient_count) AS total_patient_encounters
FROM (
    SELECT 
        provider_id,
        COUNT(DISTINCT patient_id) AS patient_count
    FROM encounters 
    WHERE provider_id IS NOT NULL
    GROUP BY provider_id
) physician_stats;

-- Query 3: Most common diagnoses by age group with medication correlation
-- Uses: patients, diagnoses, medications tables
SELECT 
    age_group,
    diagnosis_code,
    diagnosis_description,
    diagnosis_count,
    patients_with_medications,
    ROUND((patients_with_medications::DECIMAL / diagnosis_count) * 100, 2) AS medication_rate_percent
FROM (
    SELECT 
        CASE 
            WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) < 18 THEN 'Under 18'
            WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) BETWEEN 18 AND 30 THEN '18-30'
            WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) BETWEEN 31 AND 50 THEN '31-50'
            WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) BETWEEN 51 AND 70 THEN '51-70'
            ELSE 'Over 70'
        END AS age_group,
        d.diagnosis_code,
        d.diagnosis_description,
        COUNT(*) AS diagnosis_count,
        COUNT(DISTINCT m.patient_id) AS patients_with_medications
    FROM patients p
    JOIN diagnoses d ON p.patient_id = d.patient_id
    LEFT JOIN medications m ON p.patient_id = m.patient_id 
        AND m.start_date >= d.date_recorded
        AND (m.end_date IS NULL OR m.end_date >= d.date_recorded)
    GROUP BY age_group, d.diagnosis_code, d.diagnosis_description
    HAVING COUNT(*) >= 3  -- Only show diagnoses with at least 3 cases
) diagnosis_stats
ORDER BY age_group, diagnosis_count DESC;

-- Query 4: Lab value trends and abnormal results by patient demographics
-- Uses: patients, observations, encounters tables
SELECT 
    o.observation_code,
    o.observation_description,
    p.gender,
    CASE 
        WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) < 30 THEN 'Under 30'
        WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) BETWEEN 30 AND 60 THEN '30-60'
        ELSE 'Over 60'
    END AS age_group,
    COUNT(*) AS total_observations,
    ROUND(AVG(o.value_numeric), 2) AS average_value,
    ROUND(STDDEV(o.value_numeric), 2) AS std_deviation,
    COUNT(CASE WHEN o.is_abnormal = TRUE THEN 1 END) AS abnormal_count,
    ROUND(
        (COUNT(CASE WHEN o.is_abnormal = TRUE THEN 1 END)::DECIMAL / COUNT(*)) * 100, 
        2
    ) AS abnormal_percentage
FROM patients p
JOIN encounters e ON p.patient_id = e.patient_id
JOIN observations o ON e.encounter_id = o.encounter_id
WHERE o.value_numeric IS NOT NULL
GROUP BY o.observation_code, o.observation_description, p.gender, age_group
HAVING COUNT(*) >= 5  -- Only show observations with at least 5 measurements
ORDER BY o.observation_code, abnormal_percentage DESC;

-- Query 5: Patient care continuity and medication adherence patterns
-- Uses: patients, encounters, medications, procedures tables
SELECT 
    p.patient_id,
    p.first_name,
    p.last_name,
    EXTRACT(YEAR FROM AGE(p.date_of_birth)) AS age,
    encounter_span_days,
    total_encounters,
    active_medications,
    completed_procedures,
    CASE 
        WHEN encounter_span_days > 365 AND total_encounters >= 3 THEN 'High Continuity'
        WHEN encounter_span_days > 180 AND total_encounters >= 2 THEN 'Medium Continuity'
        ELSE 'Low Continuity'
    END AS care_continuity_level,
    CASE 
        WHEN active_medications > 0 THEN 'Active Treatment'
        ELSE 'No Active Treatment'
    END AS treatment_status
FROM patients p
JOIN (
    SELECT 
        patient_id,
        COUNT(*) AS total_encounters,
        EXTRACT(DAY FROM (MAX(encounter_date) - MIN(encounter_date))) AS encounter_span_days
    FROM encounters
    GROUP BY patient_id
) e_stats ON p.patient_id = e_stats.patient_id
LEFT JOIN (
    SELECT 
        patient_id,
        COUNT(*) AS active_medications
    FROM medications
    WHERE is_active = TRUE
    GROUP BY patient_id
) m_stats ON p.patient_id = m_stats.patient_id
LEFT JOIN (
    SELECT 
        patient_id,
        COUNT(*) AS completed_procedures
    FROM procedures
    GROUP BY patient_id
) proc_stats ON p.patient_id = proc_stats.patient_id
ORDER BY care_continuity_level DESC, total_encounters DESC;

-- Bonus Query: Data Quality Assessment
-- Cross-dataset validation and completeness check
SELECT 
    'patients' AS table_name,
    COUNT(*) AS total_records,
    COUNT(CASE WHEN first_name IS NULL THEN 1 END) AS missing_first_name,
    COUNT(CASE WHEN last_name IS NULL THEN 1 END) AS missing_last_name,
    COUNT(CASE WHEN date_of_birth IS NULL THEN 1 END) AS missing_dob,
    COUNT(CASE WHEN zip_code IS NULL OR zip_code = '' THEN 1 END) AS missing_zip
FROM patients

UNION ALL

SELECT 
    'observations' AS table_name,
    COUNT(*) AS total_records,
    COUNT(CASE WHEN value_numeric IS NULL AND value_text IS NULL THEN 1 END) AS missing_values,
    COUNT(CASE WHEN observation_code IS NULL THEN 1 END) AS missing_codes,
    COUNT(CASE WHEN units IS NULL THEN 1 END) AS missing_units,
    0 AS placeholder_column
FROM observations

UNION ALL

SELECT 
    'medications' AS table_name,
    COUNT(*) AS total_records,
    COUNT(CASE WHEN drug_name IS NULL THEN 1 END) AS missing_drug_name,
    COUNT(CASE WHEN dosage IS NULL THEN 1 END) AS missing_dosage,
    COUNT(CASE WHEN end_date IS NULL THEN 1 END) AS missing_end_date,
    COUNT(CASE WHEN frequency IS NULL THEN 1 END) AS missing_frequency
FROM medications;

-- Performance Query: Query execution time analysis
-- Use this to measure query performance during testing
EXPLAIN (ANALYZE, BUFFERS) 
SELECT 
    p.last_name,
    COUNT(d.diagnosis_id) AS diagnosis_count,
    COUNT(m.medication_order_id) AS medication_count
FROM patients p
LEFT JOIN diagnoses d ON p.patient_id = d.patient_id
LEFT JOIN medications m ON p.patient_id = m.patient_id
GROUP BY p.patient_id, p.last_name
HAVING COUNT(d.diagnosis_id) > 0
ORDER BY diagnosis_count DESC
LIMIT 10;
