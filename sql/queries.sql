-- Healthcare Data Engineering Project - Required Queries
-- Four cross-dataset queries meeting project requirements

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

-- Query 5: Procedure outcomes and patient health indicators by demographics
-- Uses: patients, procedures, encounters, observations tables
SELECT 
    pr.procedure_code,
    pr.procedure_description,
    p.gender,
    CASE 
        WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) < 40 THEN 'Under 40'
        WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) BETWEEN 40 AND 65 THEN '40-65'
        ELSE 'Over 65'
    END AS age_group,
    COUNT(DISTINCT pr.procedure_id) AS total_procedures,
    COUNT(DISTINCT p.patient_id) AS unique_patients,
    ROUND(AVG(EXTRACT(YEAR FROM AGE(p.date_of_birth))), 1) AS avg_patient_age,
    COUNT(CASE WHEN o.is_abnormal = TRUE THEN 1 END) AS patients_with_abnormal_results,
    ROUND(
        (COUNT(CASE WHEN o.is_abnormal = TRUE THEN 1 END)::DECIMAL / COUNT(DISTINCT p.patient_id)) * 100, 
        2
    ) AS abnormal_results_percentage,
    ROUND(AVG(o.value_numeric), 2) AS avg_lab_value
FROM patients p
JOIN procedures pr ON p.patient_id = pr.patient_id
JOIN encounters e ON p.patient_id = e.patient_id
LEFT JOIN observations o ON e.encounter_id = o.encounter_id 
    AND o.observation_code IN ('2160-0', '2345-7', '4548-4')  -- Key lab tests
    AND o.observation_datetime BETWEEN pr.date_performed - INTERVAL '30 days' 
                                    AND pr.date_performed + INTERVAL '30 days'
WHERE pr.date_performed IS NOT NULL
GROUP BY pr.procedure_code, pr.procedure_description, p.gender, age_group
HAVING COUNT(DISTINCT pr.procedure_id) >= 2  -- Only show procedures with at least 2 instances
ORDER BY total_procedures DESC, abnormal_results_percentage DESC;

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

-- Performance Query:
-- Query execution time analysis for diagnosis and medication counts by patient
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
