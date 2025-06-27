#!/usr/bin/env python3
"""
Healthcare Data Engineering Project - System Test

This script analyzes the outputs and logs from the ETL pipeline to provide:
- Comprehensive performance metrics
- Data quality assessment
- Query execution analysis
- System health overview

Best Practice: This script analyzes existing outputs rather than re-running ETL,
ensuring we test against actual production-like data and avoiding redundant processing.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import logging

class SystemTestAnalyzer:
    """Analyzes ETL pipeline outputs and generates comprehensive test reports"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logs_dir = self.project_root / "logs"
        self.output_dir = self.project_root / "output"
        self.data_processed_dir = self.project_root / "data" / "processed"
        self.quality_reports_dir = self.project_root / "data" / "quality_reports"
        
        # Setup logging for the system test itself
        self.setup_logging()
        
        # Results storage
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "etl_performance": {},
            "data_quality": {},
            "query_performance": {},
            "system_health": {},
            "issues": []
        }
    
    def setup_logging(self):
        """Setup logging for the system test"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.project_root / "tests" / "system_test.log")
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze_logs(self) -> Dict:
        """Analyze all log files and extract key metrics"""
        self.logger.info("Analyzing ETL logs...")
        
        log_files = list(self.logs_dir.glob("*.log"))
        if not log_files:
            self.test_results["issues"].append("No log files found")
            return {}
        
        # Sort by modification time to get the most recent run
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        log_analysis = {
            "total_log_files": len(log_files),
            "latest_log": log_files[0].name,
            "etl_steps": {},
            "errors": [],
            "warnings": [],
            "performance_metrics": {}
        }
        
        for log_file in log_files:
            self.analyze_single_log(log_file, log_analysis)
        
        self.test_results["etl_performance"] = log_analysis
        return log_analysis
    
    def analyze_single_log(self, log_file: Path, analysis: Dict):
        """Analyze a single log file"""
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Extract ETL step completion times
            step_pattern = r"COMPLETED - (\w+) - Duration: ([\d.]+)s"
            for match in re.finditer(step_pattern, content):
                step_name = match.group(1)
                duration = float(match.group(2))
                if step_name not in analysis["etl_steps"]:
                    analysis["etl_steps"][step_name] = []
                analysis["etl_steps"][step_name].append(duration)
            
            # Extract errors and warnings
            error_pattern = r"ERROR - (.+)"
            warning_pattern = r"WARNING - (.+)"
            
            for match in re.finditer(error_pattern, content):
                analysis["errors"].append(f"{log_file.name}: {match.group(1)}")
            
            for match in re.finditer(warning_pattern, content):
                analysis["warnings"].append(f"{log_file.name}: {match.group(1)}")
            
            # Extract data quality scores
            quality_pattern = r"Overall data quality score: ([\d.]+)%"
            quality_match = re.search(quality_pattern, content)
            if quality_match:
                analysis["performance_metrics"]["data_quality_score"] = float(quality_match.group(1))
            
            # Extract record counts from various patterns
            record_patterns = [
                r"(\d+) records? (?:loaded|processed)",
                r"Loaded (\d+) (?:patient|observation|procedure|diagnosis|medication|encounter) records?",
                r"Processed (\d+) (?:patient|observation|procedure|diagnosis|medication|encounter) records?",
                r"(\d+) (?:patient|observation|procedure|diagnosis|medication|encounter) records? loaded"
            ]
            
            for pattern in record_patterns:
                for match in re.finditer(pattern, content):
                    count = int(match.group(1))
                    if "total_records_processed" not in analysis["performance_metrics"]:
                        analysis["performance_metrics"]["total_records_processed"] = 0
                    analysis["performance_metrics"]["total_records_processed"] += count
                
        except Exception as e:
            self.test_results["issues"].append(f"Error analyzing {log_file}: {str(e)}")
    
    def analyze_data_quality(self) -> Dict:
        """Analyze data quality reports"""
        self.logger.info("Analyzing data quality reports...")
        
        quality_reports = list(self.quality_reports_dir.glob("*.json"))
        if not quality_reports:
            self.test_results["issues"].append("No quality reports found")
            return {}
        
        # Get the most recent quality report (data quality report, not load report)
        data_quality_reports = [f for f in quality_reports if "data_quality_report" in f.name]
        if not data_quality_reports:
            self.test_results["issues"].append("No data quality reports found")
            return {}
        
        latest_report = max(data_quality_reports, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(latest_report, 'r') as f:
                quality_data = json.load(f)
            
            quality_analysis = {
                "report_file": latest_report.name,
                "overall_score": quality_data.get("overall", {}).get("overall_quality_score", 0),
                "table_scores": {},
                "missing_data": {},
                "validation_issues": []
            }
            
            # Extract table-specific scores
            for table_name, table_data in quality_data.items():
                if isinstance(table_data, dict) and "data_quality_score" in table_data:
                    quality_analysis["table_scores"][table_name] = table_data["data_quality_score"]
                
                # Extract missing data info
                if isinstance(table_data, dict):
                    missing_info = {}
                    for key, value in table_data.items():
                        if "missing" in key.lower() and value != "0" and value != 0:
                            missing_info[key] = value
                    if missing_info:
                        quality_analysis["missing_data"][table_name] = missing_info
            
            # Check for validation issues
            if quality_data.get("overall", {}).get("issues_summary"):
                issues = quality_data["overall"]["issues_summary"]
                for issue, status in issues.items():
                    if not status:
                        quality_analysis["validation_issues"].append(f"{issue}: failed")
            
            self.test_results["data_quality"] = quality_analysis
            return quality_analysis
            
        except Exception as e:
            self.test_results["issues"].append(f"Error analyzing quality report: {str(e)}")
            return {}
    
    def analyze_query_performance(self) -> Dict:
        """Analyze query performance from output files"""
        self.logger.info("Analyzing query performance...")
        
        query_output_files = list(self.output_dir.glob("query_results_*.txt"))
        if not query_output_files:
            self.test_results["issues"].append("No query output files found")
            return {}
        
        # Get the most recent query output
        latest_output = max(query_output_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(latest_output, 'r') as f:
                content = f.read()
            
            query_analysis = {
                "output_file": latest_output.name,
                "queries_executed": 0,
                "query_times": {},
                "query_results": {},
                "performance_issues": []
            }
            
            # Extract query execution times - look for the pattern in the logs
            time_pattern = r"Completed: (.+?) in ([\d.]+)s"
            for match in re.finditer(time_pattern, content):
                query_name = match.group(1).strip()
                execution_time = float(match.group(2))
                query_analysis["query_times"][query_name] = execution_time
                query_analysis["queries_executed"] += 1
            
            # If no times found in output, check the logs
            if not query_analysis["query_times"]:
                log_files = list(self.logs_dir.glob("*.log"))
                if log_files:
                    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_log, 'r') as f:
                        log_content = f.read()
                    
                    for match in re.finditer(time_pattern, log_content):
                        query_name = match.group(1).strip()
                        execution_time = float(match.group(2))
                        query_analysis["query_times"][query_name] = execution_time
                        query_analysis["queries_executed"] += 1
            
            # Check for performance issues (queries taking too long)
            for query, time in query_analysis["query_times"].items():
                if time > 1.0:  # More than 1 second
                    query_analysis["performance_issues"].append(
                        f"Query '{query}' took {time:.3f}s (slow)"
                    )
            
            # Extract sample results (first few rows of each query)
            query_sections = content.split("QUERY:")
            for section in query_sections[1:]:  # Skip first empty section
                lines = section.strip().split('\n')
                if lines:
                    query_name = lines[0].strip()
                    # Get first few result lines
                    result_lines = []
                    in_results = False
                    for line in lines[1:]:
                        if '|' in line and not line.startswith('-'):
                            in_results = True
                            result_lines.append(line.strip())
                        elif in_results and not line.strip():
                            break
                        if len(result_lines) >= 3:  # Limit to 3 rows
                            break
                    
                    if result_lines:
                        query_analysis["query_results"][query_name] = result_lines[:3]
            
            self.test_results["query_performance"] = query_analysis
            return query_analysis
            
        except Exception as e:
            self.test_results["issues"].append(f"Error analyzing query output: {str(e)}")
            return {}
    
    def analyze_system_health(self) -> Dict:
        """Analyze overall system health and file integrity"""
        self.logger.info("Analyzing system health...")
        
        health_analysis = {
            "file_integrity": {},
            "directory_structure": {},
            "data_completeness": {},
            "recommendations": []
        }
        
        # Check file integrity
        expected_files = [
            ("data/processed/patients_cleaned.csv", "Processed patients data"),
            ("data/processed/observations_cleaned.csv", "Processed observations data"),
            ("data/processed/procedures_cleaned.csv", "Processed procedures data"),
            ("data/processed/diagnoses_cleaned.json", "Processed diagnoses data"),
            ("data/processed/medications_cleaned.json", "Processed medications data"),
            ("output/query_results_*.txt", "Query results"),
            ("logs/*.log", "ETL logs")
        ]
        
        for file_pattern, description in expected_files:
            files = list(self.project_root.glob(file_pattern))
            # Filter out .gitkeep files
            files = [f for f in files if not f.name.endswith('.gitkeep')]
            
            if files:
                empty_files = [f for f in files if f.stat().st_size == 0]
                non_empty_files = [f for f in files if f.stat().st_size > 0]
                if len(non_empty_files) > 0 and len(empty_files) == 0:
                    status = "OK"
                elif len(empty_files) > 0:
                    status = "WARNING"
                else:
                    status = "MISSING"
                health_analysis["file_integrity"][description] = {
                    "count": len(files),
                    "empty_files": len(empty_files),
                    "status": status
                }
                if len(empty_files) > 0:
                    health_analysis["recommendations"].append(
                        f"Found {len(empty_files)} empty {description} files"
                    )
            else:
                health_analysis["file_integrity"][description] = {
                    "count": 0,
                    "empty_files": 0,
                    "status": "MISSING"
                }
                health_analysis["recommendations"].append(f"Missing {description}")
        
        # Check data completeness
        try:
            patients_df = pd.read_csv(self.data_processed_dir / "patients_cleaned.csv")
            observations_df = pd.read_csv(self.data_processed_dir / "observations_cleaned.csv")
            procedures_df = pd.read_csv(self.data_processed_dir / "procedures_cleaned.csv")
            
            health_analysis["data_completeness"] = {
                "patients": len(patients_df),
                "observations": len(observations_df),
                "procedures": len(procedures_df),
                "total_records": len(patients_df) + len(observations_df) + len(procedures_df)
            }
            
            # Check for reasonable data volumes
            if len(patients_df) < 100:
                health_analysis["recommendations"].append("Low patient count - check data source")
            if len(observations_df) < 500:
                health_analysis["recommendations"].append("Low observation count - check data source")
                
        except Exception as e:
            health_analysis["recommendations"].append(f"Error checking data completeness: {str(e)}")
        
        self.test_results["system_health"] = health_analysis
        return health_analysis
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report"""
        self.logger.info("Generating system test report...")
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("HEALTHCARE DATA ENGINEERING PROJECT - SYSTEM TEST REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # ETL Performance Summary
        report_lines.append("ETL PERFORMANCE SUMMARY")
        report_lines.append("-" * 40)
        if self.test_results["etl_performance"]:
            perf = self.test_results["etl_performance"]
            report_lines.append(f"Total log files analyzed: {perf.get('total_log_files', 0)}")
            report_lines.append(f"Latest log: {perf.get('latest_log', 'N/A')}")
            
            if perf.get("performance_metrics"):
                metrics = perf["performance_metrics"]
                report_lines.append(f"Total records processed: {metrics.get('total_records_processed', 0):,}")
                report_lines.append(f"Data quality score: {metrics.get('data_quality_score', 0):.2f}%")
            
            if perf.get("etl_steps"):
                report_lines.append("\nETL Step Performance:")
                for step, times in perf["etl_steps"].items():
                    avg_time = sum(times) / len(times)
                    report_lines.append(f"  {step}: {avg_time:.3f}s average")
        report_lines.append("")
        
        # Data Quality Summary
        report_lines.append("DATA QUALITY SUMMARY")
        report_lines.append("-" * 40)
        if self.test_results["data_quality"]:
            quality = self.test_results["data_quality"]
            report_lines.append(f"Overall quality score: {quality.get('overall_score', 0):.2f}%")
            report_lines.append(f"Quality report: {quality.get('report_file', 'N/A')}")
            
            if quality.get("table_scores"):
                report_lines.append("\nTable Quality Scores:")
                for table, score in quality["table_scores"].items():
                    report_lines.append(f"  {table}: {score:.2f}%")
        report_lines.append("")
        
        # Query Performance Summary
        report_lines.append("QUERY PERFORMANCE SUMMARY")
        report_lines.append("-" * 40)
        if self.test_results["query_performance"]:
            query_perf = self.test_results["query_performance"]
            report_lines.append(f"Queries executed: {query_perf.get('queries_executed', 0)}")
            report_lines.append(f"Output file: {query_perf.get('output_file', 'N/A')}")
            
            if query_perf.get("query_times"):
                report_lines.append("\nQuery Execution Times:")
                for query, time in query_perf["query_times"].items():
                    status = "SLOW" if time > 1.0 else "OK"
                    report_lines.append(f"  {query}: {time:.3f}s ({status})")
            
            if query_perf.get("performance_issues"):
                report_lines.append("\nPerformance Issues:")
                for issue in query_perf["performance_issues"]:
                    report_lines.append(f"  WARNING: {issue}")
        report_lines.append("")
        
        # System Health Summary
        report_lines.append("SYSTEM HEALTH SUMMARY")
        report_lines.append("-" * 40)
        if self.test_results["system_health"]:
            health = self.test_results["system_health"]
            
            if health.get("data_completeness"):
                completeness = health["data_completeness"]
                report_lines.append(f"Total records: {completeness.get('total_records', 0):,}")
                report_lines.append(f"  - Patients: {completeness.get('patients', 0):,}")
                report_lines.append(f"  - Observations: {completeness.get('observations', 0):,}")
                report_lines.append(f"  - Procedures: {completeness.get('procedures', 0):,}")
            
            if health.get("file_integrity"):
                report_lines.append("\nFile Integrity:")
                for desc, info in health["file_integrity"].items():
                    status_icon = "OK" if info["status"] == "OK" else "WARNING" if info["status"] == "WARNING" else "ERROR"
                    report_lines.append(f"  {status_icon} {desc}: {info['count']} files")
                    if info["empty_files"] > 0:
                        report_lines.append(f"    WARNING: {info['empty_files']} empty files")
        report_lines.append("")
        
        # Issues and Recommendations
        if self.test_results["issues"] or (self.test_results["system_health"] and 
                                          self.test_results["system_health"].get("recommendations")):
            report_lines.append("ISSUES AND RECOMMENDATIONS")
            report_lines.append("-" * 40)
            
            for issue in self.test_results["issues"]:
                report_lines.append(f"ERROR: {issue}")
            
            if self.test_results["system_health"] and self.test_results["system_health"].get("recommendations"):
                for rec in self.test_results["system_health"]["recommendations"]:
                    report_lines.append(f"RECOMMENDATION: {rec}")
        else:
            report_lines.append("No issues detected - system is healthy!")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("END OF SYSTEM TEST REPORT")
        report_lines.append("=" * 80)
        
        report_content = "\n".join(report_lines)
        
        # Save report
        report_file = self.project_root / "tests" / "system_test_report.txt"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        self.logger.info(f"System test report saved to: {report_file}")
        return report_content
    
    def run_complete_analysis(self) -> Dict:
        """Run the complete system analysis"""
        self.logger.info("Starting comprehensive system test analysis...")
        
        # Run all analysis components
        self.analyze_logs()
        self.analyze_data_quality()
        self.analyze_query_performance()
        self.analyze_system_health()
        
        # Generate and save report
        report_content = self.generate_report()
        
        # Determine overall test status
        has_errors = len(self.test_results["issues"]) > 0
        has_warnings = any(
            health.get("recommendations") 
            for health in [self.test_results.get("system_health", {})]
        )
        
        if has_errors:
            self.logger.error("System test completed with ERRORS")
            return {"status": "FAILED", "results": self.test_results, "report": report_content}
        elif has_warnings:
            self.logger.warning("System test completed with WARNINGS")
            return {"status": "WARNING", "results": self.test_results, "report": report_content}
        else:
            self.logger.info("System test completed successfully")
            return {"status": "PASSED", "results": self.test_results, "report": report_content}


def main():
    """Main entry point for the system test"""
    print("Healthcare Data Engineering Project - System Test")
    print("=" * 60)
    
    # Create and run the analyzer
    analyzer = SystemTestAnalyzer()
    result = analyzer.run_complete_analysis()
    
    # Print summary
    print(f"\nTest Status: {result['status']}")
    print(f"Report saved to: tests/system_test_report.txt")
    
    # Exit with appropriate code
    if result['status'] == 'FAILED':
        sys.exit(1)
    elif result['status'] == 'WARNING':
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main() 