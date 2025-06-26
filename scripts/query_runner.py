#!/usr/bin/env python3
"""
Healthcare Data Engineering Project - Query Runner
Executes the five required cross-dataset queries
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import re
import time
from tabulate import tabulate

from config.database import db_manager

def load_queries_from_file(filepath: str) -> dict:
    """Load queries from a .sql file using comment markers."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Split by markers like -- Query 1: ... and -- Performance Query:
    pattern = re.compile(r'-- (Query \d+: .*?|Performance Query:.*?)\n', re.DOTALL)
    splits = pattern.split(content)
    queries = {}
    i = 1
    while i < len(splits):
        marker = splits[i]
        if marker is None or i+1 >= len(splits):
            break
        sql = splits[i+1]
        if marker.startswith('Performance Query'):
            queries['Performance Query'] = {'title': 'Performance Query', 'sql': sql.strip()}
        else:
            queries[marker] = {'title': marker, 'sql': sql.strip()}
        i += 2
    return queries

class QueryRunner:
    """Executes the required healthcare data queries"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        self.queries = load_queries_from_file("sql/queries.sql")
    
    def run_all_queries(self) -> bool:
        """Execute all required queries, pretty-print, and time them."""
        self.logger.info("Starting query execution...")
        results = {}
        for qnum in sorted(self.queries.keys()):
            qinfo = self.queries[qnum]
            query_name = f"{qnum}: {qinfo['title']}"
            sql = qinfo['sql']
            self.logger.info(f"Executing: {query_name}")
            start = time.time()
            try:
                result = self.db_manager.execute_query(sql)
                elapsed = time.time() - start
                results[query_name] = {
                    'description': qinfo['title'],
                    'result': result,
                    'time_seconds': round(elapsed, 3)
                }
                self.logger.info(f"Completed: {query_name} in {elapsed:.3f}s")
            except Exception as e:
                self.logger.error(f"Error in {query_name}: {e}")
                results[query_name] = {"error": str(e)}
        self._save_results(results)
        return True
    
    def query_patient_demographics(self) -> Dict[str, Any]:
        """Query 1: Patient Demographics - Average age and age range"""
        query = """
        SELECT 
            COUNT(*) as total_patients,
            ROUND(AVG(EXTRACT(YEAR FROM AGE(date_of_birth))), 2) as average_age,
            MIN(EXTRACT(YEAR FROM AGE(date_of_birth))) as min_age,
            MAX(EXTRACT(YEAR FROM AGE(date_of_birth))) as max_age,
            COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male_count,
            COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female_count
        FROM patients;
        """
        
        try:
            result = self.db_manager.execute_query(query)
            return {
                "query": "Patient Demographics",
                "description": "Average age and age range by gender",
                "result": result[0] if result else {}
            }
        except Exception as e:
            self.logger.error(f"Patient demographics query failed: {e}")
            return {"error": str(e)}
    
    def query_provider_statistics(self) -> Dict[str, Any]:
        """Query 2: Provider Statistics - Average patients per physician"""
        query = """
        SELECT 
            provider_id,
            COUNT(DISTINCT patient_id) as patient_count,
            COUNT(*) as encounter_count
        FROM encounters 
        WHERE provider_id IS NOT NULL
        GROUP BY provider_id
        ORDER BY patient_count DESC;
        """
        
        try:
            result = self.db_manager.execute_query(query)
            return {
                "query": "Provider Statistics",
                "description": "Average patients per physician",
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Provider statistics query failed: {e}")
            return {"error": str(e)}
    
    def query_diagnosis_analysis(self) -> Dict[str, Any]:
        """Query 3: Diagnosis Analysis - Most common diagnoses by age group"""
        query = """
        SELECT 
            CASE 
                WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) < 18 THEN 'Under 18'
                WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) < 30 THEN '18-29'
                WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) < 50 THEN '30-49'
                WHEN EXTRACT(YEAR FROM AGE(p.date_of_birth)) < 70 THEN '50-69'
                ELSE '70+'
            END as age_group,
            d.diagnosis_code,
            d.diagnosis_description,
            COUNT(*) as diagnosis_count
        FROM diagnoses d
        JOIN patients p ON d.patient_id = p.patient_id
        GROUP BY age_group, d.diagnosis_code, d.diagnosis_description
        ORDER BY age_group, diagnosis_count DESC;
        """
        
        try:
            result = self.db_manager.execute_query(query)
            return {
                "query": "Diagnosis Analysis",
                "description": "Most common diagnoses by age group",
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Diagnosis analysis query failed: {e}")
            return {"error": str(e)}
    
    def query_lab_results(self) -> Dict[str, Any]:
        """Query 4: Lab Results - Trends and abnormal values by demographics"""
        query = """
        SELECT 
            o.observation_code,
            o.observation_description,
            COUNT(*) as total_observations,
            COUNT(CASE WHEN o.is_abnormal = TRUE THEN 1 END) as abnormal_count,
            ROUND(AVG(o.value_numeric), 2) as average_value,
            MIN(o.value_numeric) as min_value,
            MAX(o.value_numeric) as max_value
        FROM observations o
        WHERE o.value_numeric IS NOT NULL
        GROUP BY o.observation_code, o.observation_description
        ORDER BY abnormal_count DESC;
        """
        
        try:
            result = self.db_manager.execute_query(query)
            return {
                "query": "Lab Results",
                "description": "Trends and abnormal values by demographics",
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Lab results query failed: {e}")
            return {"error": str(e)}
    
    def query_care_continuity(self) -> Dict[str, Any]:
        """Query 5: Care Continuity - Patient care patterns and medication adherence"""
        query = """
        SELECT 
            p.patient_id,
            p.first_name,
            p.last_name,
            COUNT(DISTINCT e.encounter_id) as encounter_count,
            COUNT(DISTINCT m.medication_order_id) as medication_count,
            COUNT(DISTINCT d.diagnosis_id) as diagnosis_count,
            MAX(e.encounter_date) as last_encounter,
            MIN(e.encounter_date) as first_encounter
        FROM patients p
        LEFT JOIN encounters e ON p.patient_id = e.patient_id
        LEFT JOIN medications m ON p.patient_id = m.patient_id
        LEFT JOIN diagnoses d ON p.patient_id = d.patient_id
        GROUP BY p.patient_id, p.first_name, p.last_name
        ORDER BY encounter_count DESC
        LIMIT 20;
        """
        
        try:
            result = self.db_manager.execute_query(query)
            return {
                "query": "Care Continuity",
                "description": "Patient care patterns and medication adherence",
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Care continuity query failed: {e}")
            return {"error": str(e)}
    
    def _save_results(self, results: dict) -> None:
        """Save query results to output file and print to console for debugging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"query_results_{timestamp}.txt"

        with open(output_file, 'w') as f:
            f.write("Healthcare Data Engineering Project - Query Results\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            for query_name, result in results.items():
                f.write(f"QUERY: {query_name}\n")
                f.write("-" * 40 + "\n")
                print(f"\nQUERY: {query_name}")
                print("-" * 40)
                if "error" in result:
                    f.write(f"ERROR: {result['error']}\n")
                    print(f"ERROR: {result['error']}")
                else:
                    f.write(f"Description: {result.get('description', 'N/A')}\n")
                    f.write(f"Execution Time: {result.get('time_seconds', 'N/A')} seconds\n")
                    f.write("Results:\n")
                    if query_name == 'Performance Query':
                        # Print as plain text
                        perf_result = result['result']
                        if isinstance(perf_result, list):
                            for row in perf_result:
                                line = ' | '.join(str(v) for v in row.values())
                                f.write(line + "\n")
                                print(line)
                        else:
                            f.write(str(perf_result) + "\n")
                            print(perf_result)
                    elif isinstance(result['result'], list) and result['result']:
                        table = tabulate(result['result'], headers="keys", tablefmt="grid")
                        f.write(table + "\n")
                        print(table)
                    elif isinstance(result['result'], dict):
                        for k, v in result['result'].items():
                            f.write(f"  {k}: {v}\n")
                            print(f"  {k}: {v}")
                    else:
                        f.write(str(result['result']) + "\n")
                        print(result['result'])
                f.write("\n")
                print()
        self.logger.info(f"Query results saved to: {output_file}")

if __name__ == "__main__":
    # Setup logging
    from config.logging_config import setup_logging
    setup_logging()
    
    # Run queries
    runner = QueryRunner()
    success = runner.run_all_queries()
    
    if success:
        print("Query execution completed successfully!")
    else:
        print("Query execution failed!")
        sys.exit(1) 