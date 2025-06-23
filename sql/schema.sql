-- Healthcare Data Engineering Project - PostgreSQL Schema
-- Created for cross-platform compatibility (Linux/Windows)

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Drop existing tables (for clean setup)
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS observations CASCADE;
DROP TABLE IF EXISTS procedures CASCADE;
DROP TABLE IF EXISTS medications CASCADE;
DROP TABLE IF EXISTS diagnoses CASCADE;
DROP TABLE IF EXISTS encounters CASCADE;
DROP TABLE IF EXISTS patients CASCADE;

-- Create patients table
CREATE TABLE patients (
    patient_id UUID PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('Male', 'Female', 'Other', 'Unknown')),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    phone_number VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create encounters table (extracted from SQLite data)
CREATE TABLE encounters (
    encounter_id UUID PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES patients(patient_id),
    encounter_date TIMESTAMP NOT NULL,
    encounter_type VARCHAR(100),
    provider_id VARCHAR(100),
    department VARCHAR(100),
    status VARCHAR(50) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create diagnoses table (from JSON data)
CREATE TABLE diagnoses (
    diagnosis_id UUID PRIMARY KEY,
    encounter_id UUID NOT NULL REFERENCES encounters(encounter_id),
    patient_id UUID NOT NULL REFERENCES patients(patient_id),
    diagnosis_code VARCHAR(20) NOT NULL,
    diagnosis_description TEXT NOT NULL,
    date_recorded TIMESTAMP NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create medications table (from JSON data)
CREATE TABLE medications (
    medication_order_id UUID PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES patients(patient_id),
    encounter_id UUID NOT NULL REFERENCES encounters(encounter_id),
    drug_code VARCHAR(50),
    drug_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100),
    route VARCHAR(50),
    frequency VARCHAR(100),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create procedures table
CREATE TABLE procedures (
    procedure_id UUID PRIMARY KEY,
    encounter_id UUID NOT NULL REFERENCES encounters(encounter_id),
    patient_id UUID NOT NULL REFERENCES patients(patient_id),
    procedure_code VARCHAR(20),
    procedure_description TEXT NOT NULL,
    date_performed TIMESTAMP NOT NULL,
    provider_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create observations table (lab results, vitals)
CREATE TABLE observations (
    observation_id UUID PRIMARY KEY,
    encounter_id UUID NOT NULL REFERENCES encounters(encounter_id),
    patient_id UUID NOT NULL REFERENCES patients(patient_id),
    observation_code VARCHAR(20),
    observation_description TEXT NOT NULL,
    observation_datetime TIMESTAMP NOT NULL,
    value_numeric DECIMAL(10,3),
    value_text TEXT,
    units VARCHAR(50),
    reference_range VARCHAR(100),
    is_abnormal BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create audit log table for compliance
CREATE TABLE audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    record_id UUID NOT NULL,
    user_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_values JSONB,
    new_values JSONB
);

-- Create indexes for performance
CREATE INDEX idx_patients_name ON patients(last_name, first_name);
CREATE INDEX idx_patients_dob ON patients(date_of_birth);
CREATE INDEX idx_encounters_patient ON encounters(patient_id);
CREATE INDEX idx_encounters_date ON encounters(encounter_date);
CREATE INDEX idx_diagnoses_patient ON diagnoses(patient_id);
CREATE INDEX idx_diagnoses_code ON diagnoses(diagnosis_code);
CREATE INDEX idx_medications_patient ON medications(patient_id);
CREATE INDEX idx_medications_active ON medications(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_procedures_patient ON procedures(patient_id);
CREATE INDEX idx_observations_patient ON observations(patient_id);
CREATE INDEX idx_observations_code ON observations(observation_code);
CREATE INDEX idx_observations_datetime ON observations(observation_datetime);
CREATE INDEX idx_audit_log_table_timestamp ON audit_log(table_name, timestamp);

-- Create views for common queries
CREATE VIEW patient_summary AS
SELECT 
    p.patient_id,
    p.first_name,
    p.last_name,
    p.date_of_birth,
    EXTRACT(YEAR FROM AGE(p.date_of_birth)) AS age,
    p.gender,
    COUNT(DISTINCT e.encounter_id) AS total_encounters,
    COUNT(DISTINCT d.diagnosis_id) AS total_diagnoses,
    COUNT(DISTINCT m.medication_order_id) AS total_medications,
    MAX(e.encounter_date) AS last_visit
FROM patients p
LEFT JOIN encounters e ON p.patient_id = e.patient_id
LEFT JOIN diagnoses d ON p.patient_id = d.patient_id
LEFT JOIN medications m ON p.patient_id = m.patient_id
GROUP BY p.patient_id, p.first_name, p.last_name, p.date_of_birth, p.gender;

-- Create view for active medications
CREATE VIEW active_medications AS
SELECT 
    m.*,
    p.first_name,
    p.last_name,
    e.encounter_date
FROM medications m
JOIN patients p ON m.patient_id = p.patient_id
JOIN encounters e ON m.encounter_id = e.encounter_id
WHERE m.is_active = TRUE;

-- Create functions for data quality checks
CREATE OR REPLACE FUNCTION check_referential_integrity() 
RETURNS TABLE(table_name TEXT, issue_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 'diagnoses_orphaned'::TEXT, COUNT(*)
    FROM diagnoses d
    WHERE NOT EXISTS (SELECT 1 FROM patients p WHERE p.patient_id = d.patient_id)
    
    UNION ALL
    
    SELECT 'medications_orphaned'::TEXT, COUNT(*)
    FROM medications m
    WHERE NOT EXISTS (SELECT 1 FROM patients p WHERE p.patient_id = m.patient_id)
    
    UNION ALL
    
    SELECT 'observations_orphaned'::TEXT, COUNT(*)
    FROM observations o
    WHERE NOT EXISTS (SELECT 1 FROM patients p WHERE p.patient_id = o.patient_id);
END;
$$ LANGUAGE plpgsql;

-- Create trigger function for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, record_id, old_values)
        VALUES (TG_TABLE_NAME, TG_OP, OLD.patient_id, row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, operation, record_id, old_values, new_values)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.patient_id, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, record_id, new_values)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.patient_id, row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create audit triggers for compliance
CREATE TRIGGER audit_patients AFTER INSERT OR UPDATE OR DELETE ON patients
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_diagnoses AFTER INSERT OR UPDATE OR DELETE ON diagnoses
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_medications AFTER INSERT OR UPDATE OR DELETE ON medications
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Create user roles for security
CREATE ROLE healthcare_admin;
CREATE ROLE healthcare_analyst;
CREATE ROLE healthcare_readonly;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO healthcare_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO healthcare_admin;

GRANT SELECT, INSERT, UPDATE ON patients, encounters, diagnoses, medications, procedures, observations TO healthcare_analyst;
GRANT SELECT ON audit_log TO healthcare_analyst;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO healthcare_readonly;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create updated_at triggers
CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_encounters_updated_at BEFORE UPDATE ON encounters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE patients IS 'Core patient demographic and contact information';
COMMENT ON TABLE encounters IS 'Medical encounters/visits with healthcare providers';
COMMENT ON TABLE diagnoses IS 'Medical diagnoses associated with encounters';
COMMENT ON TABLE medications IS 'Prescribed medications with dosage and timing';
COMMENT ON TABLE procedures IS 'Medical procedures performed during encounters';
COMMENT ON TABLE observations IS 'Lab results, vital signs, and other measurements';
COMMENT ON TABLE audit_log IS 'Audit trail for compliance and security monitoring';

-- Final data quality constraints
ALTER TABLE patients ADD CONSTRAINT valid_zip_code 
    CHECK (zip_code IS NULL OR zip_code ~ '^\d{5}(-\d{4})?$');

ALTER TABLE observations ADD CONSTRAINT valid_numeric_or_text 
    CHECK (value_numeric IS NOT NULL OR value_text IS NOT NULL);

-- Database setup complete
SELECT 'Healthcare database schema created successfully' AS status;
