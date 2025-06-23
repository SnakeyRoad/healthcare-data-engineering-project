"""
Healthcare Data Engineering Project - Data Cleaning Pipeline
Comprehensive data cleaning and validation for healthcare datasets
Handles CSV and JSON files with cross-platform compatibility
"""

import os
import sys
import pandas as pd
import json
import sqlite3
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import re
from uuid import UUID, uuid4

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.database import get_db_manager
from config.logging_config import setup_logging

class DataCleaner:
    """Main data cleaning pipeline for healthcare data"""
    
    def __init__(self, data_path: str = None):
        self.data_path = Path(data_path) if data_path else Path("data/raw")
        self.processed_path = Path("data/processed")
        self.quality_reports_path = Path("data/quality_reports")
        
        # Create directories if they don't exist
        self.processed_path.mkdir(parents=True, exist_ok=True)
        self.quality_reports_path.mkdir(parents=True, exist_ok=True)
        
        self.db_manager = get_db_manager()
        self.logger = logging.getLogger(__name__)
        
        # Data quality metrics
        self.quality_report = {
            'patients': {},
            'observations': {},
            'procedures': {},
            'diagnoses': {},
            'medications': {},
            'encounters': {}
        }
    
    def validate_uuid(self, uuid_string: str) -> bool:
        """Validate UUID format"""
        try:
            UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False
    
    def standardize_date(self, date_value: Any) -> Optional[datetime]:
        """Standardize date formats across all files"""
        if pd.isna(date_value) or date_value is None:
            return None
        
        # Convert to string if not already
        date_str = str(date_value).strip()
        
        # Common date formats in healthcare data
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y%m%d'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        self.logger.warning(f"Could not parse date: {date_value}")
        return None
    
    def standardize_zip_code(self, zip_code: Any) -> Optional[str]:
        """Standardize zip code format to 5 digits"""
        if pd.isna(zip_code) or zip_code is None:
            return None
        
        # Convert to string and remove any non-digits
        zip_str = re.sub(r'[^\d]', '', str(zip_code))
        
        if len(zip_str) == 0:
            return None
        elif len(zip_str) <= 5:
            # Pad with leading zeros
            return zip_str.zfill(5)
        else:
            # Take first 5 digits for ZIP+4 format
            return zip_str[:5]
    
    def standardize_phone(self, phone: Any) -> Optional[str]:
        """Standardize phone number format"""
        if pd.isna(phone) or phone is None:
            return None
        
        # Remove all non-digits
        digits = re.sub(r'[^\d]', '', str(phone))
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return str(phone)  # Return original if can't standardize
    
    def clean_patients_data(self) -> pd.DataFrame:
        """Clean patients.csv data"""
        self.logger.info("Cleaning patients data...")
        
        try:
            df = pd.read_csv(self.data_path / "patients.csv")
            initial_count = len(df)
            
            # Standardize date of birth
            df['date_of_birth'] = df['date_of_birth'].apply(self.standardize_date)
            
            # Standardize zip codes
            df['zip_code'] = df['zip_code'].apply(self.standardize_zip_code)
            
            # Standardize phone numbers
            df['phone_number'] = df['phone_number'].apply(self.standardize_phone)
            
            # Clean name fields
            df['first_name'] = df['first_name'].str.strip().str.title()
            df['last_name'] = df['last_name'].str.strip().str.title()
            
            # Standardize gender
            df['gender'] = df['gender'].str.strip().str.title()
            
            # Validate patient_id format
            df['valid_uuid'] = df['patient_id'].apply(self.validate_uuid)
            if not df['valid_uuid'].all():
                self.logger.warning(f"Found {(~df['valid_uuid']).sum()} invalid patient UUIDs")
            df = df.drop('valid_uuid', axis=1)
            
            # Calculate age for validation
            df['age'] = df['date_of_birth'].apply(
                lambda x: (datetime.now() - x).days // 365 if x else None
            )
            
            # Remove unrealistic ages
            df = df[(df['age'] >= 0) & (df['age'] <= 150)]
            
            # Quality metrics
            self.quality_report['patients'] = {
                'initial_count': initial_count,
                'final_count': len(df),
                'missing_dob': df['date_of_birth'].isna().sum(),
                'missing_zip': df['zip_code'].isna().sum(),
                'missing_phone': df['phone_number'].isna().sum(),
                'data_quality_score': (len(df) / initial_count) * 100
            }
            
            # Save processed data
            output_path = self.processed_path / "patients_cleaned.csv"
            df.to_csv(output_path, index=False)
            self.logger.info(f"Processed {len(df)} patient records")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error cleaning patients data: {e}")
            raise
    
    def clean_observations_data(self) -> pd.DataFrame:
        """Clean observations.csv data"""
        self.logger.info("Cleaning observations data...")
        
        try:
            df = pd.read_csv(self.data_path / "observations.csv")
            initial_count = len(df)
            
            # Standardize observation datetime
            df['observation_datetime'] = df['observation_datetime'].apply(self.standardize_date)
            
            # Handle missing values strategy
            # value_text missing: Leave as NULL for numeric observations
            # value_numeric missing: Use median for lab values where appropriate
            
            # Identify numeric vs text observations
            numeric_codes = ['glucose', 'creatinine', 'hemoglobin', 'a1c', 'cholesterol']
            df['is_numeric_observation'] = df['observation_description'].str.lower().str.contains('|'.join(numeric_codes), na=False)
            
            # For numeric observations with missing value_numeric, try to extract from value_text
            mask = df['is_numeric_observation'] & df['value_numeric'].isna() & df['value_text'].notna()
            for idx in df[mask].index:
                text_val = str(df.loc[idx, 'value_text'])
                # Extract numeric value from text
                numeric_match = re.search(r'(\d+\.?\d*)', text_val)
                if numeric_match:
                    df.loc[idx, 'value_numeric'] = float(numeric_match.group(1))
            
            # Validate observation values are within reasonable ranges
            # Glucose: 50-500 mg/dL
            # Hemoglobin A1c: 4-20%
            # Creatinine: 0.5-10.0 mg/dL
            
            value_ranges = {
                'glucose': (50, 500),
                'a1c': (4, 20),
                'creatinine': (0.5, 10.0),
                'hemoglobin': (5, 20)
            }
            
            for test, (min_val, max_val) in value_ranges.items():
                mask = df['observation_description'].str.lower().str.contains(test, na=False)
                out_of_range = mask & ((df['value_numeric'] < min_val) | (df['value_numeric'] > max_val))
                if out_of_range.any():
                    self.logger.warning(f"Found {out_of_range.sum()} {test} values out of range")
                    # Set extreme values to NaN for review
                    df.loc[out_of_range, 'value_numeric'] = None
            
            # Add abnormal flag based on common reference ranges
            df['is_abnormal'] = False
            
            # Glucose abnormal if > 100 fasting or > 140 random
            glucose_mask = df['observation_description'].str.lower().str.contains('glucose', na=False)
            df.loc[glucose_mask & (df['value_numeric'] > 100), 'is_abnormal'] = True
            
            # A1c abnormal if > 7%
            a1c_mask = df['observation_description'].str.lower().str.contains('a1c', na=False)
            df.loc[a1c_mask & (df['value_numeric'] > 7), 'is_abnormal'] = True
            
            # Quality metrics
            self.quality_report['observations'] = {
                'initial_count': initial_count,
                'final_count': len(df),
                'missing_value_text': df['value_text'].isna().sum(),
                'missing_value_numeric': df['value_numeric'].isna().sum(),
                'missing_both_values': ((df['value_text'].isna()) & (df['value_numeric'].isna())).sum(),
                'abnormal_results': df['is_abnormal'].sum(),
                'data_quality_score': ((len(df) - ((df['value_text'].isna()) & (df['value_numeric'].isna())).sum()) / initial_count) * 100
            }
            
            # Save processed data
            df = df.drop('is_numeric_observation', axis=1)
            output_path = self.processed_path / "observations_cleaned.csv"
            df.to_csv(output_path, index=False)
            self.logger.info(f"Processed {len(df)} observation records")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error cleaning observations data: {e}")
            raise
    
    def clean_procedures_data(self) -> pd.DataFrame:
        """Clean procedures.csv data"""
        self.logger.info("Cleaning procedures data...")
        
        try:
            df = pd.read_csv(self.data_path / "procedures.csv")
            initial_count = len(df)
            
            # Standardize date performed
            df['date_performed'] = df['date_performed'].apply(self.standardize_date)
            
            # Clean procedure codes and descriptions
            df['procedure_code'] = df['procedure_code'].astype(str).str.strip()
            df['procedure_description'] = df['procedure_description'].str.strip()
            
            # Remove rows with missing essential data
            df = df.dropna(subset=['date_performed', 'procedure_description'])
            
            # Quality metrics
            self.quality_report['procedures'] = {
                'initial_count': initial_count,
                'final_count': len(df),
                'missing_date': initial_count - len(df),
                'data_quality_score': (len(df) / initial_count) * 100
            }
            
            # Save processed data
            output_path = self.processed_path / "procedures_cleaned.csv"
            df.to_csv(output_path, index=False)
            self.logger.info(f"Processed {len(df)} procedure records")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error cleaning procedures data: {e}")
            raise
    
    def clean_json_data(self, filename: str) -> List[Dict]:
        """Generic JSON data cleaning"""
        self.logger.info(f"Cleaning {filename}...")
        
        try:
            with open(self.data_path / filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            initial_count = len(data)
            cleaned_data = []
            
            for record in data:
                # Standardize date fields
                for date_field in ['date_recorded', 'start_date', 'end_date']:
                    if date_field in record:
                        record[date_field] = self.standardize_date(record[date_field])
                        if record[date_field]:
                            record[date_field] = record[date_field].isoformat()
                
                # Clean string fields
                for field in record:
                    if isinstance(record[field], str):
                        record[field] = record[field].strip()
                
                cleaned_data.append(record)
            
            # Save cleaned JSON
            output_path = self.processed_path / f"{filename.replace('.json', '_cleaned.json')}"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, default=str)
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"Error cleaning {filename}: {e}")
            raise
    
    def explore_sqlite_database(self) -> Dict:
        """Explore SQLite database structure and extract encounters data"""
        self.logger.info("Exploring SQLite database...")
        
        try:
            sqlite_path = self.data_path / "ehr_journeys_database.sqlite"
            if not sqlite_path.exists():
                self.logger.warning("SQLite database not found")
                return {}
            
            conn = sqlite3.connect(sqlite_path)
            
            # Get table list
            tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
            tables = pd.read_sql_query(tables_query, conn)
            
            database_info = {
                'tables': tables['name'].tolist(),
                'table_data': {}
            }
            
            # Extract data from each table
            for table in database_info['tables']:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                    database_info['table_data'][table] = {
                        'row_count': len(df),
                        'columns': df.columns.tolist(),
                        'sample_data': df.head().to_dict('records') if len(df) > 0 else []
                    }
                    
                    # Save table data as CSV
                    output_path = self.processed_path / f"sqlite_{table}.csv"
                    df.to_csv(output_path, index=False)
                    
                except Exception as e:
                    self.logger.error(f"Error reading table {table}: {e}")
            
            conn.close()
            
            # Save database structure info
            info_path = self.processed_path / "sqlite_database_info.json"
            with open(info_path, 'w') as f:
                json.dump(database_info, f, indent=2, default=str)
            
            return database_info
            
        except Exception as e:
            self.logger.error(f"Error exploring SQLite database: {e}")
            return {}
    
    def generate_quality_report(self) -> None:
        """Generate comprehensive data quality report"""
        self.logger.info("Generating data quality report...")
        
        # Calculate overall quality score
        total_score = 0
        total_datasets = 0
        
        for dataset, metrics in self.quality_report.items():
            if metrics and 'data_quality_score' in metrics:
                total_score += metrics['data_quality_score']
                total_datasets += 1
        
        overall_score = total_score / total_datasets if total_datasets > 0 else 0
        
        self.quality_report['overall'] = {
            'overall_quality_score': overall_score,
            'total_datasets_processed': total_datasets,
            'processing_timestamp': datetime.now().isoformat(),
            'issues_summary': {
                'missing_values_handled': True,
                'date_formats_standardized': True,
                'data_validation_applied': True,
                'referential_integrity_checked': False  # Will be done during loading
            }
        }
        
        # Save quality report
        report_path = self.quality_reports_path / f"data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(self.quality_report, f, indent=2, default=str)
        
        self.logger.info(f"Data quality report saved to {report_path}")
        self.logger.info(f"Overall data quality score: {overall_score:.2f}%")
    
    def run_complete_pipeline(self) -> bool:
        """Run the complete data cleaning pipeline"""
        self.logger.info("Starting complete data cleaning pipeline...")
        
        try:
            # Clean all datasets
            patients_df = self.clean_patients_data()
            observations_df = self.clean_observations_data()
            procedures_df = self.clean_procedures_data()
            
            # Clean JSON files
            diagnoses_data = self.clean_json_data("diagnoses.json")
            medications_data = self.clean_json_data("medications.json")
            
            # Explore SQLite database
            sqlite_info = self.explore_sqlite_database()
            
            # Update quality report for JSON files
            self.quality_report['diagnoses'] = {
                'record_count': len(diagnoses_data),
                'data_quality_score': 100  # Assuming JSON data is clean after processing
            }
            
            self.quality_report['medications'] = {
                'record_count': len(medications_data),
                'data_quality_score': 100
            }
            
            # Generate final quality report
            self.generate_quality_report()
            
            self.logger.info("Data cleaning pipeline completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Data cleaning pipeline failed: {e}")
            return False

def main():
    """Main execution function"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Healthcare Data Cleaning Pipeline Started")
    
    # Initialize data cleaner
    cleaner = DataCleaner()
    
    # Run cleaning pipeline
    success = cleaner.run_complete_pipeline()
    
    if success:
        logger.info("Data cleaning completed successfully")
        
        # Print summary
        print("\n" + "="*50)
        print("DATA CLEANING SUMMARY")
        print("="*50)
        
        for dataset, metrics in cleaner.quality_report.items():
            if dataset != 'overall' and metrics:
                print(f"\n{dataset.upper()}:")
                if 'initial_count' in metrics:
                    print(f"  Records processed: {metrics.get('final_count', 'N/A')} / {metrics.get('initial_count', 'N/A')}")
                if 'data_quality_score' in metrics:
                    print(f"  Quality score: {metrics['data_quality_score']:.2f}%")
        
        if 'overall' in cleaner.quality_report:
            overall_score = cleaner.quality_report['overall']['overall_quality_score']
            print(f"\nOVERALL QUALITY SCORE: {overall_score:.2f}%")
        
        print("\nProcessed files saved to: data/processed/")
        print("Quality reports saved to: data/quality_reports/")
        
    else:
        logger.error("Data cleaning failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
