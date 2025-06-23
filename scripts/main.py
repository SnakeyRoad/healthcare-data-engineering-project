#!/usr/bin/env python3
"""
Healthcare Data Engineering Project - Main Execution Script
Cross-platform main entry point for the ETL pipeline
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.logging_config import setup_logging, log_system_info
from config.database import get_db_manager, init_database
from scripts.data_cleaning import DataCleaner
from scripts.data_loader import DataLoader
from scripts.query_runner import QueryRunner

class HealthcareETLPipeline:
    """Main ETL pipeline orchestrator"""
    
    def __init__(self, data_path: str = "data/raw"):
        self.data_path = Path(data_path)
        self.logger = logging.getLogger(__name__)
        self.db_manager = get_db_manager()
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        self.logger.info("Checking prerequisites...")
        
        # Check if data directory exists
        if not self.data_path.exists():
            self.logger.error(f"Data directory not found: {self.data_path}")
            return False
        
        # Check for required data files
        required_files = [
            "patients.csv",
            "observations.csv", 
            "procedures.csv",
            "diagnoses.json",
            "medications.json"
        ]
        
        missing_files = []
        for file in required_files:
            if not (self.data_path / file).exists():
                missing_files.append(file)
        
        if missing_files:
            self.logger.error(f"Missing required data files: {missing_files}")
            return False
        
        # Check database connectivity
        if not self.db_manager.config.test_connection():
            self.logger.error("Database connection failed")
            return False
        
        self.logger.info("All prerequisites met")
        return True
    
    def setup_database(self) -> bool:
        """Initialize database schema"""
        self.logger.info("Setting up database...")
        
        try:
            success = init_database()
            if success:
                self.logger.info("Database setup completed")
                return True
            else:
                self.logger.error("Database setup failed")
                return False
        except Exception as e:
            self.logger.error(f"Database setup error: {e}")
            return False
    
    def run_data_cleaning(self) -> bool:
        """Execute data cleaning pipeline"""
        self.logger.info("Starting data cleaning...")
        
        try:
            cleaner = DataCleaner(str(self.data_path))
            success = cleaner.run_complete_pipeline()
            
            if success:
                self.logger.info("Data cleaning completed")
                return True
            else:
                self.logger.error("Data cleaning failed")
                return False
        except Exception as e:
            self.logger.error(f"Data cleaning error: {e}")
            return False
    
    def run_data_loading(self) -> bool:
        """Execute data loading pipeline"""
        self.logger.info("Starting data loading...")
        
        try:
            loader = DataLoader()
            success = loader.load_all_data()
            
            if success:
                self.logger.info("Data loading completed")
                return True
            else:
                self.logger.error("Data loading failed")
                return False
        except Exception as e:
            self.logger.error(f"Data loading error: {e}")
            return False
    
    def run_queries(self) -> bool:
        """Execute required queries"""
        self.logger.info("Running project queries...")
        
        try:
            query_runner = QueryRunner()
            success = query_runner.run_all_queries()
            
            if success:
                self.logger.info("Query execution completed")
                return True
            else:
                self.logger.error("Query execution failed")
                return False
        except Exception as e:
            self.logger.error(f"Query execution error: {e}")
            return False
    
    def generate_final_report(self) -> bool:
        """Generate final project report"""
        self.logger.info("Generating final report...")
        
        try:
            # Get database statistics
            stats = self.db_manager.get_database_stats()
            
            # Generate summary report
            report_path = Path("docs/final_report.md")
            report_path.parent.mkdir(exist_ok=True)
            
            with open(report_path, 'w') as f:
                f.write("# Healthcare Data Engineering Project - Final Report\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("## Database Statistics\n\n")
                for table, info in stats.items():
                    f.write(f"- **{table}**: {info['row_count']} records\n")
                
                f.write("\n## Data Quality Summary\n\n")
                f.write("- Data cleaning: Completed\n")
                f.write("- Data loading: Completed\n")
                f.write("- Query execution: Completed\n")
                f.write("- Referential integrity: Validated\n")
            
            self.logger.info(f"Final report generated: {report_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
            return False
    
    def run_complete_pipeline(self) -> bool:
        """Run the complete ETL pipeline"""
        self.logger.info("🚀 Starting Healthcare Data Engineering Pipeline")
        
        steps = [
            ("Prerequisites Check", self.check_prerequisites),
            ("Database Setup", self.setup_database),
            ("Data Cleaning", self.run_data_cleaning),
            ("Data Loading", self.run_data_loading),
            ("Query Execution", self.run_queries),
            ("Final Report", self.generate_final_report)
        ]
        
        for step_name, step_function in steps:
            self.logger.info(f"Executing: {step_name}")
            
            try:
                success = step_function()
                if not success:
                    self.logger.error(f"Pipeline failed at: {step_name}")
                    return False
                self.logger.info(f"Completed: {step_name}")
                
            except Exception as e:
                self.logger.error(f"Error in {step_name}: {e}")
                return False
        
        self.logger.info("Pipeline completed successfully!")
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Healthcare Data Engineering ETL Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/main.py                    # Run complete pipeline
  python scripts/main.py --data-path ./data/raw --log-level DEBUG
  python scripts/main.py --step cleaning   # Run only data cleaning
  python scripts/main.py --step loading    # Run only data loading
  python scripts/main.py --step queries    # Run only queries
        """
    )
    
    parser.add_argument(
        '--data-path',
        default='data/raw',
        help='Path to raw data files (default: data/raw)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--step',
        choices=['cleaning', 'loading', 'queries', 'all'],
        default='all',
        help='Run specific pipeline step (default: all)'
    )
    
    parser.add_argument(
        '--skip-prerequisites',
        action='store_true',
        help='Skip prerequisites check'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for results (default: output)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    logger = logging.getLogger(__name__)
    
    # Log system information
    log_system_info()
    
    # Create output directory
    Path(args.output_dir).mkdir(exist_ok=True)
    
    # Initialize pipeline
    pipeline = HealthcareETLPipeline(args.data_path)
    
    logger.info(f"Starting pipeline with data path: {args.data_path}")
    logger.info(f"Log level: {args.log_level}")
    logger.info(f"Step: {args.step}")
    
    try:
        if args.step == 'all':
            success = pipeline.run_complete_pipeline()
        else:
            # Run individual steps
            if not args.skip_prerequisites:
                if not pipeline.check_prerequisites():
                    logger.error("Prerequisites check failed")
                    return 1
            
            if args.step == 'cleaning':
                success = pipeline.run_data_cleaning()
            elif args.step == 'loading':
                success = pipeline.run_data_loading()
            elif args.step == 'queries':
                success = pipeline.run_queries()
            else:
                logger.error(f"Unknown step: {args.step}")
                return 1
        
        if success:
            logger.info("Pipeline execution completed successfully!")
            
            # Print summary
            print("\n" + "="*60)
            print("HEALTHCARE DATA ENGINEERING PIPELINE SUMMARY")
            print("="*60)
            
            if args.step == 'all' or args.step == 'loading':
                stats = pipeline.db_manager.get_database_stats()
                print("\nDatabase Statistics:")
                total_records = 0
                for table, info in stats.items():
                    if info['row_count'] > 0:
                        print(f"  • {table}: {info['row_count']:,} records")
                        total_records += info['row_count']
                
                print(f"\nTotal Records Processed: {total_records:,}")
            
            print(f"\nProcessed files: data/processed/")
            print(f"Quality reports: data/quality_reports/")
            print(f"Logs: logs/")
            print(f"Output: {args.output_dir}/")
            
            return 0
        else:
            logger.error("Pipeline execution failed!")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    # Import datetime here to avoid circular imports
    from datetime import datetime
    exit(main())
