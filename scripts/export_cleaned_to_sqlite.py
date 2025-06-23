import pandas as pd
import sqlite3
import json
from pathlib import Path

# Paths
processed_dir = Path('data/processed')
sqlite_path = processed_dir / 'ehr_journeys_database.sqlite'

# Remove existing file if exists
if sqlite_path.exists():
    sqlite_path.unlink()

# Connect to new SQLite DB
conn = sqlite3.connect(sqlite_path)

# Export patients
patients_csv = processed_dir / 'patients_cleaned.csv'
if patients_csv.exists():
    df_patients = pd.read_csv(patients_csv)
    df_patients.to_sql('patients', conn, if_exists='replace', index=False)

# Export diagnoses
# JSON file

diagnoses_json = processed_dir / 'diagnoses_cleaned.json'
if diagnoses_json.exists():
    with open(diagnoses_json) as f:
        diagnoses_data = json.load(f)
    df_diagnoses = pd.DataFrame(diagnoses_data)
    df_diagnoses.to_sql('diagnoses', conn, if_exists='replace', index=False)

# Export medications
medications_json = processed_dir / 'medications_cleaned.json'
if medications_json.exists():
    with open(medications_json) as f:
        medications_data = json.load(f)
    df_medications = pd.DataFrame(medications_data)
    df_medications.to_sql('medications', conn, if_exists='replace', index=False)

# Export procedures
procedures_csv = processed_dir / 'procedures_cleaned.csv'
if procedures_csv.exists():
    df_procedures = pd.read_csv(procedures_csv)
    df_procedures.to_sql('procedures', conn, if_exists='replace', index=False)

# Export observations
observations_csv = processed_dir / 'observations_cleaned.csv'
if observations_csv.exists():
    df_observations = pd.read_csv(observations_csv)
    df_observations.to_sql('observations', conn, if_exists='replace', index=False)

# Export sqlite_encounters if present
encounters_csv = processed_dir / 'sqlite_encounters.csv'
if encounters_csv.exists():
    df_encounters = pd.read_csv(encounters_csv)
    df_encounters.to_sql('encounters', conn, if_exists='replace', index=False)

conn.close()

print(f"Exported cleaned data to {sqlite_path}") 