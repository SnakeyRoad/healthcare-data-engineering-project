# Healthcare Data Engineering Project

## Overview

This project implements a complete ETL (Extract, Transform, Load) pipeline for synthetic healthcare data using Python, PostgreSQL, and Docker. The pipeline covers data cleaning, validation, database loading, analytical queries, and reporting. The codebase is designed for reproducibility and cross-platform compatibility (Linux, macOS, Windows).

---

## Project Status

### Completed
- Docker and environment setup
- Database configuration and connection management
- Data cleaning and validation pipeline
- Data loading pipeline with error handling and logging
- Query runner for analytical and performance queries
- Output formatting for human-readable results
- Security framework (role-based access, .env config)
- Comprehensive documentation and reproducibility instructions

### In Progress / To Do
- Security framework and compliance documentation (expand in docs)
- System integration and deployment (productionization, CI/CD)
- PostgreSQL schema optimization and advanced indexing
- Performance benchmarking and reporting
- Additional data quality analysis and test case development
- Documentation of design decisions, database comparisons, and rationale

---

## Assignment Requirements & Coverage

- **Analysis of datasets:** Data types, structure, missing values, and rationale for PostgreSQL (relational) choice are documented.
- **Database comparison:** (To do) Add a section comparing PostgreSQL, SQLite, and MongoDB, and justify the choice.
- **System design:** Architecture, security, and distribution described in this README and code comments.
- **Data security policy:** .env-based secrets, role-based access, and audit logging implemented; further documentation needed.
- **Realization:** All ETL steps are implemented as Python scripts, with Dockerized database and pgAdmin for management.
- **Queries:** At least four cross-dataset queries, including required demographic and provider statistics, are implemented and output in readable tables.
- **Performance analysis:** Query plan and timing are included in the output.
- **Test report:** Output files and logs provide evidence of successful runs and performance.

---

## Project Structure

```
healthcare_data_project/
├── config/                 # Python config modules (database, logging, settings)
├── data/
│   ├── raw/               # Original synthetic data files (CSV, JSON, SQLite)
│   ├── processed/         # Cleaned data after ETL
│   └── quality_reports/   # Data quality and load reports
├── docs/                  # Documentation and design notes
├── logs/                  # Application logs
├── output/                # Query results and reports
├── scripts/
│   ├── data_cleaning.py   # Data cleaning and validation pipeline
│   ├── data_loader.py     # Loads cleaned data into PostgreSQL
│   ├── query_runner.py    # Runs analytical and performance queries
│   └── main.py            # Optional main entry point
├── sql/
│   ├── schema.sql         # Database schema (tables, constraints)
│   ├── queries.sql        # Analytical and performance queries
│   └── test_data.sql/     # Optional test data
├── tests/                 # Unit and integration tests
├── Dockerfile             # Python environment for Docker
├── docker-compose.yml     # Multi-container orchestration (Postgres, pgAdmin)
├── requirements.txt       # Python dependencies
├── .env.example           # Example environment configuration
└── README.md              # Project documentation (this file)
```

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
- Copy `.env.example` to `.env` and edit as needed.
- The `.env` file is loaded automatically by the Python scripts and Docker Compose.

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
Copy `.env.example` to `.env` and update credentials as needed.

### 4. Start Docker Services
```bash
docker compose up -d
```

### 5. Run the ETL Pipeline
```bash
source venv/bin/activate  # Always activate venv first
python3 scripts/data_cleaning.py
python3 scripts/data_loader.py
python3 scripts/query_runner.py
```

### 6. View Results
- Query results are saved in the `output/` directory.
- Logs are in `logs/`.
- Data quality reports are in `data/quality_reports/`.

### 7. Access pgAdmin
- Open [http://localhost:5050](http://localhost:5050)
- Login with credentials from your `.env` file.

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

## What Remains To Be Done

- Expand documentation on security framework and compliance (GDPR, ISO, etc.).
- Add a section comparing PostgreSQL, SQLite, and MongoDB, and justify the choice of PostgreSQL.
- Add more advanced performance benchmarking and reporting.
- Add more data quality analysis and test case development.
- Document design decisions, system integration, and deployment steps.
- Finalize and polish all documentation for submission.

---

## Assignment Coverage Checklist

- [x] Data analysis and cleaning
- [x] Database schema and loading
- [x] Analytical and performance queries
- [x] Output formatting and reporting
- [x] Security and .env configuration
- [x] Dockerized, cross-platform setup
- [ ] Database comparison and rationale
- [ ] Advanced security and compliance documentation
- [ ] Performance benchmarking and test report
- [ ] Final integration and deployment documentation

---

## Contact

For questions or support, please contact the project maintainer.

---

**This project is for educational purposes as part of a university data science program.**
