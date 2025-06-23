"""
Healthcare Data Engineering Project - Data Loading Pipeline
Loads cleaned data into PostgreSQL database with validation and error handling
"""

import os
import sys
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import uuid
from sqlalchemy.exc import IntegrityError

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.database import get_db_manager
from config.logging_config import PerformanceLogger, DataQualityLogger

class DataLoader:
    """Main data loading pipeline for healthcare data"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.logger = logging.getLogger(__name__)
        self.quality_logger = DataQualityLogger()
        
        self.processed_path = Path("data/processed")
        self.batch_size = int(os.getenv('BATCH_SIZE', '1000'))
        
        # Loading statistics
        self.load_stats = {
            'patients': {'loaded': 0, 'errors': 0},
            'encounters': {'loaded': 0, 'errors': 0},
            'diagnoses': {'loaded': 0, 'errors': 0},
            'medications': {'loaded': 0, 'errors': 0},
            'procedures': {'loaded': 0, 'errors': 0},
            'observations': {'loaded': 0, 'errors': 0}
        }
    
    def validate_data_integrity(self) -> bool:
        """Validate data integrity before loading"""
        self.logger.info("Validating data integrity...")
        
        try:
            # Check if processed files exist
            required_files = [
                "patients_cleaned.csv",
                "observations_cleaned.csv",
                "procedures_cleaned.csv",
                "diagnoses_cleaned.json",
                "medications_cleaned.json"
            ]
            
            missing_files = []
            for file in required_files:
                if not (self.processed_path / file).exists():
                    missing_files.append(file)
            
            if missing_files:
                self.logger.error(f"Missing processed files: {missing_files}")
                return False
            
            # Validate file integrity
            patients_df = pd.read_csv(self.processed_path / "patients_cleaned.csv")
            if len(patients_df) == 0:
                self.logger.error("Patients file is empty")
                return False
            
            self.logger.info("Data integrity validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Data integrity validation failed: {e}")
            return False
    
    def load_patients(self) -> bool:
        """Load patients data into database"""
        self.logger.info("Loading patients data...")
        
        try:
            with PerformanceLogger("load_patients"):
                df = pd.read_csv(self.processed_path / "patients_cleaned.csv")
                
                # Prepare data for insertion
                records = []
                for _, row in df.iterrows():
                    record = {
                        'patient_id': row['patient_id'],
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'date_of_birth': row['date_of_birth'],
                        'gender': row['gender'],
                        'address': row.get('address'),
                        'city': row.get('city'),
                        'state': row.get('state'),
                        'zip_code': row.get('zip_code'),
                        'phone_number': row.get('phone_number')
                    }
                    records.append(record)
                
                # Insert in batches
                self._batch_insert('patients', records)
                
                self.load_stats['patients']['loaded'] = len(records)
                self.logger.info(f"Loaded {len(records)} patient records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to load patients: {e}")
            self.load_stats['patients']['errors'] += 1
            return False
    
    def load_encounters(self) -> bool:
        """Load encounters data from SQLite database"""
        self.logger.info("Loading encounters data...")
        
        try:
            with PerformanceLogger("load_encounters"):
                # Check if we have extracted SQLite data
                sqlite_files = list(self.processed_path.glob("sqlite_*.csv"))
                
                if not sqlite_files:
                    self.logger.warning("No SQLite encounter data found, creating default encounters")
                    return self._create_default_encounters()
                
                # Load encounters from SQLite data
                encounters_file = None
                for file in sqlite_files:
                    if 'encounter' in file.name.lower() or 'visit' in file.name.lower():
                        encounters_file = file
                        break
                
                if encounters_file:
                    df = pd.read_csv(encounters_file)
                    records = self._prepare_encounters_from_sqlite(df)
                else:
                    # Create encounters based on other data
                    return self._create_default_encounters()
                
                self._batch_insert('encounters', records)
                self.load_stats['encounters']['loaded'] = len(records)
                self.logger.info(f"Loaded {len(records)} encounter records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to load encounters: {e}")
            self.load_stats['encounters']['errors'] += 1
            return False
    
    def _create_default_encounters(self) -> bool:
        """Create default encounters based on other data"""
        self.logger.info("Creating default encounters...")
        
        try:
            # Get unique patient-date combinations from diagnoses and procedures
            encounters = set()
            
            # From diagnoses
            with open(self.processed_path / "diagnoses_cleaned.json", 'r') as f:
                diagnoses = json.load(f)
            
            for diag in diagnoses:
                if diag.get('patient_id') and diag.get('date_recorded'):
                    encounters.add((diag['patient_id'], diag['date_recorded'][:10]))  # Date only
            
            # From procedures
            procedures_df = pd.read_csv(self.processed_path / "procedures_cleaned.csv")
            for _, row in procedures_df.iterrows():
                if row['patient_id'] and row['date_performed']:
                    encounters.add((row['patient_id'], row['date_performed'][:10]))
            
            # Create encounter records
            records = []
            for patient_id, encounter_date in encounters:
                record = {
                    'encounter_id': str(uuid.uuid4()),
                    'patient_id': patient_id,
                    'encounter_date': encounter_date,
                    'encounter_type': 'Outpatient Visit',
                    'provider_id': f"PROV_{hash(patient_id) % 100:03d}",
                    'department': 'Primary Care',
                    'status': 'completed'
                }
                records.append(record)
            
            self._batch_insert('encounters', records)
            self.load_stats['encounters']['loaded'] = len(records)
            self.logger.info(f"Created {len(records)} default encounter records")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create default encounters: {e}")
            return False
    
    def load_diagnoses(self) -> bool:
        """Load diagnoses data from JSON"""
        self.logger.info("Loading diagnoses data...")
        
        try:
            with PerformanceLogger("load_diagnoses"):
                with open(self.processed_path / "diagnoses_cleaned.json", 'r') as f:
                    data = json.load(f)
                
                # Enrich with encounter_id mapping for fallback
                encounter_map = self._get_encounter_mapping()
                
                records = []
                for item in data:
                    # Use existing encounter_id if available, otherwise find by date
                    encounter_id = item.get('encounter_id')
                    if not encounter_id:
                        encounter_id = self._find_encounter_id(
                            item['patient_id'], 
                            item['date_recorded'], 
                            encounter_map
                        )
                    
                    if encounter_id:
                        record = {
                            'diagnosis_id': item['diagnosis_id'],
                            'encounter_id': encounter_id,
                            'patient_id': item['patient_id'],
                            'diagnosis_code': item['diagnosis_code'],
                            'diagnosis_description': item['diagnosis_description'],
                            'date_recorded': item['date_recorded'],
                            'is_primary': True  # Assume first diagnosis is primary
                        }
                        records.append(record)
                
                self._batch_insert('diagnoses', records)
                self.load_stats['diagnoses']['loaded'] = len(records)
                self.logger.info(f"Loaded {len(records)} diagnosis records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to load diagnoses: {e}")
            self.load_stats['diagnoses']['errors'] += 1
            return False
    
    def load_medications(self) -> bool:
        """Load medications data from JSON"""
        self.logger.info("Loading medications data...")
        
        try:
            with PerformanceLogger("load_medications"):
                with open(self.processed_path / "medications_cleaned.json", 'r') as f:
                    data = json.load(f)
                
                encounter_map = self._get_encounter_mapping()
                
                records = []
                for item in data:
                    # Use existing encounter_id if available, otherwise find by date
                    encounter_id = item.get('encounter_id')
                    if not encounter_id:
                        encounter_id = self._find_encounter_id(
                            item['patient_id'], 
                            item['start_date'], 
                            encounter_map
                        )
                    
                    if encounter_id:
                        record = {
                            'medication_order_id': item['medication_order_id'],
                            'patient_id': item['patient_id'],
                            'encounter_id': encounter_id,
                            'drug_code': item.get('drug_code'),
                            'drug_name': item['drug_name'],
                            'dosage': item.get('dosage'),
                            'route': item.get('route'),
                            'frequency': item.get('frequency'),
                            'start_date': item['start_date'],
                            'end_date': item.get('end_date')
                        }
                        records.append(record)
                
                self._batch_insert('medications', records)
                self.load_stats['medications']['loaded'] = len(records)
                self.logger.info(f"Loaded {len(records)} medication records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to load medications: {e}")
            self.load_stats['medications']['errors'] += 1
            return False
    
    def load_procedures(self) -> bool:
        """Load procedures data from CSV"""
        self.logger.info("Loading procedures data...")
        
        try:
            with PerformanceLogger("load_procedures"):
                df = pd.read_csv(self.processed_path / "procedures_cleaned.csv")
                
                records = []
                for _, row in df.iterrows():
                    # Use existing encounter_id from the data
                    encounter_id = row.get('encounter_id')
                    
                    if encounter_id:
                        record = {
                            'procedure_id': row['procedure_id'],
                            'encounter_id': encounter_id,
                            'patient_id': row['patient_id'],
                            'procedure_code': row.get('procedure_code'),
                            'procedure_description': row['procedure_description'],
                            'date_performed': row['date_performed'],
                            'provider_id': f"PROV_{hash(row['patient_id']) % 100:03d}"
                        }
                        records.append(record)
                
                self._batch_insert('procedures', records)
                self.load_stats['procedures']['loaded'] = len(records)
                self.logger.info(f"Loaded {len(records)} procedure records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to load procedures: {e}")
            self.load_stats['procedures']['errors'] += 1
            return False
    
    def load_observations(self) -> bool:
        """Load observations data from CSV"""
        self.logger.info("Loading observations data...")
        
        try:
            with PerformanceLogger("load_observations"):
                df = pd.read_csv(self.processed_path / "observations_cleaned.csv")
                
                records = []
                for _, row in df.iterrows():
                    # Use existing encounter_id from the data
                    encounter_id = row.get('encounter_id')
                    
                    if encounter_id:
                        record = {
                            'observation_id': row['observation_id'],
                            'encounter_id': encounter_id,
                            'patient_id': row['patient_id'],
                            'observation_code': row.get('observation_code'),
                            'observation_description': row['observation_description'],
                            'observation_datetime': row['observation_datetime'],
                            'value_numeric': row.get('value_numeric') if pd.notna(row.get('value_numeric')) else None,
                            'value_text': row.get('value_text') if pd.notna(row.get('value_text')) else None,
                            'units': row.get('units'),
                            'is_abnormal': row.get('is_abnormal', False)
                        }
                        records.append(record)
                
                self._batch_insert('observations', records)
                self.load_stats['observations']['loaded'] = len(records)
                self.logger.info(f"Loaded {len(records)} observation records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to load observations: {e}")
            self.load_stats['observations']['errors'] += 1
            return False
    
    def _get_encounter_mapping(self) -> Dict:
        """Get patient-date to encounter_id mapping"""
        query = """
        SELECT encounter_id, patient_id, DATE(encounter_date) as encounter_date
        FROM encounters
        """
        results = self.db_manager.execute_query(query)
        
        mapping = {}
        for row in results:
            key = f"{row['patient_id']}_{row['encounter_date']}"
            mapping[key] = row['encounter_id']
        
        return mapping
    
    def _find_encounter_id(self, patient_id: str, date_str: str, encounter_map: Dict) -> Optional[str]:
        """Find encounter_id for patient and date"""
        if not date_str:
            return None
        
        # Extract date part
        date_part = date_str[:10] if len(date_str) >= 10 else date_str
        key = f"{patient_id}_{date_part}"
        
        return encounter_map.get(key)
    
    def _batch_insert(self, table_name: str, records: List[Dict]) -> None:
        """Insert records in batches"""
        if not records:
            return
        
        total_batches = (len(records) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            try:
                # Prepare SQL for batch insert
                columns = list(batch[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                sql = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
                """
                
                # Prepare values
                values = []
                for record in batch:
                    values.append([record[col] for col in columns])
                
                # Execute batch insert
                with self.db_manager.config.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.executemany(sql, values)
                        conn.commit()
                
                self.logger.debug(f"Inserted batch {batch_num}/{total_batches} for {table_name}")
                
            except Exception as e:
                self.logger.error(f"Batch insert failed for {table_name}: {e}")
                raise
    
    def validate_referential_integrity(self) -> bool:
        """Validate referential integrity after loading"""
        self.logger.info("Validating referential integrity...")
        
        try:
            integrity_results = self.db_manager.verify_referential_integrity()
            
            # Handle case where verify_referential_integrity returns empty dict
            if not integrity_results:
                self.logger.warning("Referential integrity check returned no results")
                return False
            
            total_issues = sum(integrity_results.values())
            if total_issues == 0:
                self.logger.info("Referential integrity validation passed")
                return True
            else:
                self.logger.warning(f"Found {total_issues} referential integrity issues")
                for table, issues in integrity_results.items():
                    if issues > 0:
                        self.logger.warning(f"  {table}: {issues} orphaned records")
                return False
                
        except Exception as e:
            self.logger.error(f"Referential integrity validation failed: {e}")
            return False
    
    def generate_load_report(self) -> None:
        """Generate loading report"""
        self.logger.info("Generating load report...")
        
        total_loaded = sum(stats['loaded'] for stats in self.load_stats.values())
        total_errors = sum(stats['errors'] for stats in self.load_stats.values())
        
        try:
            database_stats = self.db_manager.get_database_stats()
        except Exception as e:
            self.logger.warning(f"Could not get database stats: {e}")
            database_stats = {}
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_records_loaded': total_loaded,
                'total_errors': total_errors,
                'success_rate': (total_loaded / (total_loaded + total_errors)) * 100 if total_loaded + total_errors > 0 else 0
            },
            'details': self.load_stats,
            'database_stats': database_stats
        }
        
        # Save report
        report_path = Path("data/quality_reports") / f"load_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Load report saved to {report_path}")
    
    def load_all_data(self) -> bool:
        """Load all data in correct order"""
        self.logger.info("🚀 Starting data loading pipeline...")
        
        # Validate data integrity first
        if not self.validate_data_integrity():
            return False
        
        # Loading order is important due to foreign key constraints
        load_steps = [
            ("Patients", self.load_patients),
            ("Encounters", self.load_encounters),
            ("Diagnoses", self.load_diagnoses),
            ("Medications", self.load_medications),
            ("Procedures", self.load_procedures),
            ("Observations", self.load_observations)
        ]
        
        for step_name, step_function in load_steps:
            self.logger.info(f"Loading: {step_name}")
            
            try:
                success = step_function()
                if not success:
                    self.logger.error(f"Failed to load: {step_name}")
                    return False
                self.logger.info(f"Completed: {step_name}")
                
            except Exception as e:
                self.logger.error(f"Error loading {step_name}: {e}")
                return False
        
        # Validate referential integrity
        if not self.validate_referential_integrity():
            self.logger.warning("Referential integrity issues detected")
        
        # Generate final report
        self.generate_load_report()
        
        self.logger.info("Data loading completed successfully!")
        return True

    def _prepare_encounters_from_sqlite(self, df):
        """Prepare encounter records from SQLite-extracted DataFrame, skipping rows with missing dates"""
        records = []
        for _, row in df.iterrows():
            # Handle different possible date column names
            encounter_date = (row.get('encounter_date') or 
                            row.get('visit_date') or 
                            row.get('admission_date'))
            
            if not encounter_date or pd.isna(encounter_date):
                continue  # Skip rows with missing date
                
            record = {
                'encounter_id': str(row.get('encounter_id', uuid.uuid4())),
                'patient_id': row.get('patient_id'),
                'encounter_date': encounter_date,
                'encounter_type': row.get('encounter_type') or row.get('visit_type', 'Outpatient Visit'),
                'provider_id': (row.get('provider_id') or 
                               row.get('attending_physician_id') or 
                               f"PROV_{hash(row.get('patient_id')) % 100:03d}"),
                'department': row.get('department', 'Primary Care'),
                'status': row.get('status', 'completed')
            }
            records.append(record)
        return records

def main():
    """Main execution function"""
    from config.logging_config import setup_logging
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Healthcare Data Loading Pipeline Started")
    
    loader = DataLoader()
    success = loader.load_all_data()
    
    if success:
        logger.info("Data loading completed successfully")
        
        # Print summary
        print("\n" + "="*50)
        print("DATA LOADING SUMMARY")
        print("="*50)
        
        total_loaded = sum(stats['loaded'] for stats in loader.load_stats.values())
        total_errors = sum(stats['errors'] for stats in loader.load_stats.values())
        
        for table, stats in loader.load_stats.items():
            if stats['loaded'] > 0:
                print(f"{table}: {stats['loaded']:,} records loaded")
        
        print(f"\nTOTAL: {total_loaded:,} records loaded")
        if total_errors > 0:
            print(f"ERRORS: {total_errors} errors encountered")
        
        return 0
    else:
        logger.error("Data loading failed")
        return 1

if __name__ == "__main__":
    exit(main())
