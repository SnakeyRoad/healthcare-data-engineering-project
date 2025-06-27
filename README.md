# Healthcare Data Engineering Project

## Overview

This project implements a complete ETL (Extract, Transform, Load) pipeline for synthetic healthcare data using Python, PostgreSQL, and Docker. The pipeline covers data cleaning, validation, database loading, analytical queries, and reporting. The codebase is designed for reproducibility and cross-platform compatibility (Linux, macOS, Windows).

**Project Status: COMPLETED** ✅

---

## Project Status

### Completed ✅
- Docker and environment setup
- Database configuration and connection management
- Data cleaning and validation pipeline
- Data loading pipeline with error handling and logging
- Query runner for analytical and performance queries
- Output formatting for human-readable results
- Security framework (role-based access, .env config)
- Comprehensive documentation and reproducibility instructions
- **Database comparison and rationale** (see `docs/database_comparison.md`)
- **System test and performance reporting** (see below)
- **Security and compliance documentation** (see `docs/security-policy.md`)
- **All assignment requirements fulfilled**

### Portfolio Documentation
All logs, output files, and comprehensive documentation can be found in the portfolio directory, including:
- Complete ETL pipeline logs
- Query execution results and performance metrics
- Data quality reports and validation results
- System test reports and analysis
- Technical diagrams and architecture documentation

---

## Assignment Requirements & Coverage

- **Analysis of datasets:** Data types, structure, missing values, and rationale for PostgreSQL (relational) choice are documented.
- **Database comparison:** See `docs/database_comparison.md` for a comparison of PostgreSQL, SQLite, and MongoDB, and justification for the choice.
- **System design:** Architecture, security, and distribution described in this README and code comments.
- **Data security policy:** .env-based secrets, role-based access, and audit logging implemented; see `docs/security-policy.md` for details.
- **Realization:** All ETL steps are implemented as Python scripts, with Dockerized database and pgAdmin for management.
- **Queries:** At least four cross-dataset queries, including required demographic and provider statistics, are implemented and output in readable tables.
- **Performance analysis:** Query plan and timing are included in the output.
- **Test report:** Output files and logs provide evidence of successful runs and performance. See the system test section below.

---

## Project Structure

```
healthcare_data_project/
├── config/                 # Python config modules (database, logging, settings)
├── data/
│   ├── raw/               # Original synthetic data files (CSV, JSON, SQLite)
│   ├── processed/         # Cleaned data after ETL
│   └── quality_reports/   # Data quality and load reports
├── docs/                  # Documentation and design notes (see below)
├── logs/                  # Application logs
├── output/                # Query results and reports
├── scripts/
│   ├── data_cleaning.py   # Data cleaning and validation pipeline
│   ├── data_loader.py     # Loads cleaned data into PostgreSQL
│   └── query_runner.py    # Runs analytical and performance queries
├── sql/
│   ├── schema.sql         # Database schema (tables, constraints)
│   ├── queries.sql        # Analytical and performance queries
│   └── test_data.sql/     # Optional test data
├── tests/                 # System and integration tests (see tests/README.md)
├── Dockerfile             # Python environment for Docker
├── docker-compose.yml     # Multi-container orchestration (Postgres, pgAdmin)
├── requirements.txt       # Python dependencies
├── .env.example           # Example environment configuration
└── README.md              # Project documentation (this file)
```

---

## Documentation

- **Architecture diagrams, data flow, and design:** See `docs/` for PNG diagrams and markdown explanations.
- **Database comparison:** See `docs/database_comparison.md`.
- **System distribution:** See `docs/distribution.md`.
- **Security policy:** See `docs/security-policy.md`.

---

## System Test and Reporting

A comprehensive system test is provided to validate the entire ETL pipeline, aggregate logs and outputs, and measure query performance.

- **Script:** `tests/system_test.py`
- **Report:** `tests/system_test_report.txt`

**To run the system test:**
```bash
python tests/system_test.py
```
This will analyze the latest ETL run, check file integrity, summarize performance, and generate a detailed report.

See `tests/README.md` for more details.

---

## File/Directory Explanations

- **config/**: Python modules for database and logging configuration.
- **data/raw/**: Source data files (CSV, JSON, SQLite) for patients, encounters, etc.
- **data/processed/**: Cleaned and validated data, ready for loading.
- **data/quality_reports/**: JSON reports on data quality and load status.
- **docs/**: Additional documentation, design notes, and assignment analysis.
- **logs/**: Log files generated during ETL and query runs.
- **output/**: Human-readable query results and performance reports.
- **scripts/data_cleaning.py**: Cleans and validates raw data, outputs to processed/.
- **scripts/data_loader.py**: Loads processed data into the PostgreSQL database.
- **scripts/query_runner.py**: Runs all analytical and performance queries, outputs results.
- **sql/schema.sql**: Defines the normalized database schema.
- **sql/queries.sql**: Contains all analytical and performance queries, marked for loader.
- **Dockerfile**: Builds a minimal Python environment for running the ETL pipeline.
- **docker-compose.yml**: Orchestrates PostgreSQL and pgAdmin containers.
- **requirements.txt**: Lists all Python dependencies, including tabulate for output formatting.
- **.env.example**: Template for environment variables (database credentials, ports, etc.).
- **README.md**: This documentation file.

---

## Environment and .env Handling

- All sensitive configuration (database credentials, ports, etc.) is managed via a `.env` file.
- The `.env` file is included in repository since it does not contain sensitve information (that can't be extracted from the dockercompose file anyway)
  and is loaded automatically by the Python scripts and Docker Compose.

---

## Running the Project

### 1. Clone the Repository
```bash
git clone <repository-url>
cd healthcare_data_project
```

### 2. Set Up the Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create/Edit the .env File
```
`.env` file is included in the repository
```

### 4. Start Docker Services
```bash
docker compose up -d
```

### 5. Run the ETL Pipeline
The ETL pipeline consists of three independent scripts that should be run in sequence:

```bash
source venv/bin/activate  # Always activate venv first

# Step 1: Data Cleaning
python3 scripts/data_cleaning.py

# Step 2: Data Loading
python3 scripts/data_loader.py

# Step 3: Query Execution
python3 scripts/query_runner.py
```

**Note:** Each script can be run independently. The pipeline is designed to be modular, allowing you to run individual steps as needed.

### 6. View Results
- Query results are saved in the `output/` directory.
- Logs are in `logs/`.
- Data quality reports are in `data/quality_reports/`.

### 7. Access pgAdmin (Optional)
- Open [http://localhost:5050](http://localhost:5050)
- Login with credentials from your `.env` file. (pgAdmin might ask for masterpwd, set this to own preference)

**Note:** pgAdmin is optional for the assignment. The ETL pipeline works perfectly without it, and all database operations can be verified through the query runner output.

### 8. Verify Database Connectivity (Alternative to pgAdmin)
If you have trouble with pgAdmin, you can verify database connectivity using command-line tools:

#### Option A: Using psql (if installed)
```bash
# Test connection and view tables
PGPASSWORD=secure_password_2024 psql -h localhost -p 5432 -U healthcare_admin -d healthcare_db -c "\dt"

# Test a simple query
PGPASSWORD=secure_password_2024 psql -h localhost -p 5432 -U healthcare_admin -d healthcare_db -c "SELECT COUNT(*) FROM patients;"

# View table statistics
PGPASSWORD=secure_password_2024 psql -h localhost -p 5432 -U healthcare_admin -d healthcare_db -c "SELECT table_name, (SELECT count(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count FROM information_schema.tables t WHERE table_schema = 'public' ORDER BY table_name;"
```

#### Option B: Using Docker exec (if psql not installed)
```bash
# Test connection from within the PostgreSQL container
docker exec healthcare_postgres psql -U healthcare_admin -d healthcare_db -c "SELECT version();"

# View all tables
docker exec healthcare_postgres psql -U healthcare_admin -d healthcare_db -c "\dt"

# Check data counts
docker exec healthcare_postgres psql -U healthcare_admin -d healthcare_db -c "SELECT 'patients' as table_name, count(*) as row_count FROM patients UNION ALL SELECT 'diagnoses', count(*) FROM diagnoses UNION ALL SELECT 'medications', count(*) FROM medications UNION ALL SELECT 'observations', count(*) FROM observations UNION ALL SELECT 'procedures', count(*) FROM procedures ORDER BY table_name;"
```

#### Option C: Using the Query Runner Script
The most reliable way to verify everything is working:
```bash
# Run the query runner to execute all analytical queries
python3 scripts/query_runner.py
```

This will execute all cross-dataset queries and show that the database is fully functional with all data loaded correctly.

---

## Windows Compatibility

- **Python code:** All scripts use cross-platform libraries and avoid OS-specific paths. The use of `os.path` and `pathlib` ensures compatibility.
- **Docker Compose:** Works on Windows with Docker Desktop. The `Dockerfile` uses only standard Python and system packages available on all platforms.
- **Dockerfile:** Uses `python:3.11-slim` as the base image, which is Linux-based, but this is standard for Docker and works identically on Windows via Docker Desktop.
- **No hardcoded Linux paths** are used in the Python code or Dockerfile.
- **.env handling:** Works on all platforms; just ensure line endings are correct (use a text editor that supports Unix line endings if needed).

**Known caveats:**
- On Windows, always use Docker Desktop (not WSL1) for full compatibility.
- File permissions and user creation in the Dockerfile are Linux-specific, but this does not affect Windows users running containers via Docker Desktop.
- Always activate the Python virtual environment before running scripts.

---

## Project Completion Summary

This healthcare data engineering project has been successfully completed with all requirements fulfilled:

- **Complete ETL Pipeline**: End-to-end data processing from raw sources to analytical insights
- **High Data Quality**: 99.82% quality score with comprehensive validation
- **Excellent Performance**: Sub-second processing and < 20ms query execution
- **Robust Architecture**: Containerized, scalable, and maintainable design
- **Comprehensive Testing**: Automated validation and performance monitoring
- **Complete Documentation**: Architecture diagrams, implementation guides, and comprehensive analysis

**All logs, output files, and comprehensive documentation can be found in the portfolio directory for detailed review and analysis.**

---

## Assignment Coverage Checklist

- [x] Data analysis and cleaning
- [x] Database schema and loading
- [x] Analytical and performance queries
- [x] Output formatting and reporting
- [x] Security and .env configuration
- [x] Dockerized, cross-platform setup
- [x] Database comparison and rationale
- [x] Advanced security and compliance documentation
- [x] Performance benchmarking and test report
- [x] Final integration and deployment documentation
- [x] Portfolio completion

---

## Contact

For questions or support, please contact the project maintainer.

---

**This project is for educational purposes as part of a university data science program.**
