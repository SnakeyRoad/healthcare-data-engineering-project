# Healthcare Data Engineering Project

A comprehensive ETL pipeline for healthcare data processing using PostgreSQL, Python, and Docker.

## Team Members
- **Christian** (Team Lead) - Infrastructure, Security, Integration
- **Kian Azizpour** - Database Design, Query Implementation
- **Kiana** - Data Validation, Quality Assessment

## Project Overview

This project implements a complete data engineering pipeline for healthcare data, including:
- Data cleaning and validation
- PostgreSQL database design with proper normalization
- ETL pipeline with error handling and logging
- GDPR-compliant security framework
- Performance monitoring and quality assessment

## Quick Start

### Prerequisites
- Docker Desktop (Windows) or Docker CE (Linux)
- Python 3.9+
- Git

### Setup
```bash
# Clone or extract project
cd healthcare_data_project

# Copy environment template
cp .env.example .env
# Edit .env with your database passwords

# Start database services
docker-compose up -d

# Install Python dependencies
pip install -r requirements.txt

# Place your data files in data/raw/
# - patients.csv
# - observations.csv
# - procedures.csv
# - diagnoses.json
# - medications.json
# - ehr_journeys_database.sqlite
```

### Run Pipeline
```bash
# Run complete pipeline
python scripts/main.py

# Or run individual steps
python scripts/main.py --step cleaning
python scripts/main.py --step loading
python scripts/main.py --step queries
```

## Project Structure

```
healthcare_data_project/
├── data/
│   ├── raw/                    # Original data files
│   ├── processed/              # Cleaned data
│   └── quality_reports/        # Data quality assessments
├── scripts/
│   ├── main.py                # Main execution script
│   ├── data_cleaning.py       # Data cleaning pipeline
│   ├── data_loader.py         # Database loading
│   ├── query_runner.py        # Query execution
│   └── data_validation.py     # Validation rules
├── sql/
│   ├── schema.sql             # Database schema
│   └── queries.sql            # Project queries
├── config/
│   ├── database.py            # Database configuration
│   ├── logging_config.py      # Logging setup
│   └── settings.py            # Application settings
├── tests/                     # Test suites
├── docs/                      # Documentation
└── logs/                      # Application logs
```

## Data Processing Pipeline

### 1. Data Cleaning
- **Input**: Raw CSV and JSON files
- **Process**: 
  - Standardize date formats
  - Validate and clean zip codes
  - Handle missing values (861 missing value_text entries)
  - Normalize phone numbers and names
  - Extract structured data from SQLite database
- **Output**: Cleaned files in `data/processed/`

### 2. Database Loading
- **Process**:
  - Load patients first (referential integrity)
  - Create encounters from multiple data sources
  - Load diagnoses, medications, procedures, observations
  - Validate foreign key relationships
- **Features**:
  - Batch processing for performance
  - Error handling and rollback
  - Comprehensive logging

### 3. Query Execution
Five cross-dataset queries required by project:
1. **Patient Demographics**: Average age and age range
2. **Provider Statistics**: Average patients per physician
3. **Diagnosis Analysis**: Most common diagnoses by age group
4. **Lab Results**: Trends and abnormal values by demographics
5. **Care Continuity**: Patient care patterns and medication adherence

## Database Schema

### Core Tables
- **patients**: Demographics and contact information
- **encounters**: Medical visits and provider interactions
- **diagnoses**: Medical conditions with ICD-10 codes
- **medications**: Prescriptions with dosage and timing
- **procedures**: Medical procedures and treatments
- **observations**: Lab results and vital signs

### Security Features
- Role-based access control (admin, analyst, readonly)
- Audit logging for compliance
- Data encryption capabilities
- GDPR compliance framework

## Data Quality Metrics

### Completeness
- **Patients**: 100% complete core fields
- **Observations**: 97.3% have values (861/886 missing value_text handled)
- **Medications**: 100% have drug names and start dates
- **Procedures**: 100% have descriptions and dates

### Validation Rules
- Patient ages: 0-150 years
- Glucose values: 50-500 mg/dL
- A1c values: 4-20%
- UUID format validation for all IDs
- Referential integrity across all tables

## Performance Targets

- **Data Loading**: < 10 minutes for complete dataset
- **Query Execution**: < 5 seconds per query
- **Data Validation**: < 2 minutes for quality checks
- **Memory Usage**: < 2GB during processing

## Security Implementation

### Level 1 (Implemented)
- Environment variable configuration
- Database password protection
- User role separation
- Basic access logging

### Level 2 (Documented)
- Column-level encryption for sensitive data
- Advanced audit trails
- GDPR data deletion procedures
- Multi-factor authentication

## Team Responsibilities

### Christian (Team Lead)
- [x] Docker and environment setup
- [x] Database configuration and connection management
- [x] Data cleaning pipeline implementation
- [x] Data loading pipeline with error handling
- [ ] Security framework and compliance documentation
- [ ] System integration and deployment

### Kian (Database Specialist)
- [ ] PostgreSQL schema customization and optimization
- [ ] Query implementation and performance tuning
- [ ] JSON to relational transformation logic
- [ ] Database integration testing
- [ ] Performance benchmarking

### Kiana (Data Quality Analyst)
- [ ] Data validation rules implementation
- [ ] Quality assessment metrics and reporting
- [ ] Test case development for data integrity
- [ ] Documentation of data quality findings
- [ ] SQLite database exploration and mapping

## Development Workflow

### Environment Setup
```bash
# Start development environment
docker-compose --profile dev up -d

# Access database
# pgAdmin: http://localhost:5050
# Username: admin@healthcare.local
# Password: admin_password_2024

# Access PostgreSQL directly
docker exec -it healthcare_postgres psql -U healthcare_admin -d healthcare_db
```

### Code Quality
- PEP 8 compliance for Python code
- Comprehensive error handling
- Structured logging throughout
- Unit tests for critical functions
- Code review requirements

### Testing Strategy
```bash
# Run data quality tests
python -m pytest tests/test_data_quality.py

# Run query validation tests
python -m pytest tests/test_queries.py

# Run security tests
python -m pytest tests/test_security.py

# Run complete test suite
python -m pytest tests/ -v
```

## Troubleshooting

### Common Issues

**Docker Permission Errors (Linux)**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

**Database Connection Failed**
- Check `.env` file has correct passwords
- Verify Docker containers are running: `docker-compose ps`
- Check ports aren't in use: `netstat -tulpn | grep 5432`

**Data Loading Errors**
- Ensure data files are in `data/raw/`
- Check file permissions: `chmod 644 data/raw/*`
- Verify data cleaning completed successfully

**Windows Path Issues**
- Use forward slashes in paths
- Set `DATA_PATH` in `.env` with full Windows path
- Use PowerShell instead of Command Prompt

### Performance Optimization

**Slow Query Performance**
```sql
-- Check index usage
EXPLAIN ANALYZE SELECT * FROM patient_summary;

-- Monitor database performance
SELECT * FROM pg_stat_user_tables;
```

**Memory Issues**
- Reduce `BATCH_SIZE` in `.env`
- Process data in smaller chunks
- Monitor with: `docker stats healthcare_postgres`

## Compliance and Documentation

### GDPR Compliance
- Purpose limitation: Educational data processing only
- Data minimization: Using provided dataset without collection
- Access control: Role-based permissions implemented
- Audit logging: All database operations tracked
- Data retention: Automatic cleanup after project completion

### Technical Documentation
- **System Design**: `docs/system_design.md`
- **Security Policy**: `docs/security_policy.md`
- **API Documentation**: `docs/api_documentation.md`

## Monitoring and Logging

### Log Files
- **Main Pipeline**: `logs/healthcare_etl_*.log`
- **Data Quality**: `logs/data_quality.log`
- **Database Operations**: `logs/database_operations.log`
- **Security Events**: `logs/security_audit.log`
- **Performance**: `logs/performance.log`

### Monitoring Dashboards
Access pgAdmin at http://localhost:5050 for:
- Database performance metrics
- Query execution plans
- Connection monitoring
- Storage usage statistics

## Final Deliverables

### Technical Artifacts
- [x] Complete ETL pipeline with error handling
- [x] Normalized PostgreSQL database schema
- [ ] Five cross-dataset queries with performance metrics
- [x] Data quality reports and validation framework
- [x] Security implementation and compliance documentation

### Assessment Documentation
- [ ] System architecture and design decisions
- [ ] Data quality assessment and remediation strategies
- [ ] Performance analysis and scalability considerations
- [ ] Security policy and GDPR compliance procedures

## Project Timeline

### Week 1: Foundation (Days 1-7)
- [x] Environment setup and Docker configuration
- [x] Database schema implementation
- [x] Data cleaning pipeline development
- [ ] Initial data loading and validation

### Week 2: Implementation (Days 8-14)
- [ ] Query implementation and optimization
- [ ] Performance testing and benchmarking
- [ ] Security documentation and compliance
- [ ] Final integration and presentation preparation

## Success Criteria

- ✅ All data quality issues identified and resolved
- ✅ Complete database schema with proper relationships
- ⏳ Five queries executing within performance targets
- ✅ Comprehensive security framework implemented
- ⏳ Professional documentation and presentation ready

## Contact and Support

For technical issues or questions:
- **Team Lead**: Christian
- **Database Issues**: Kian
- **Data Quality**: Kiana

## License

This project is for educational purposes as part of a university data science program.
