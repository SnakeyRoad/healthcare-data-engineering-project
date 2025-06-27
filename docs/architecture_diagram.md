# Healthcare Data Engineering Project - Architecture Diagram

## System Architecture Overview

```mermaid
graph TB
    %% Styling
    classDef dataSource fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000
    classDef etlProcess fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000
    classDef database fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px,color:#000
    classDef output fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef query fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#000
    classDef container fill:#f1f8e9,stroke:#33691e,stroke-width:2px,color:#000

    %% Data Sources
    subgraph "Data Sources"
        CSV[CSV Files<br/>patients.csv<br/>procedures.csv<br/>observations.csv]:::dataSource
        JSON[JSON Files<br/>diagnoses.json<br/>medications.json]:::dataSource
        SQLITE[SQLite Database<br/>ehr_journeys_database.sqlite]:::dataSource
    end

    %% ETL Pipeline
    subgraph "ETL Pipeline"
        CLEAN[Data Cleaning<br/>data_cleaning.py<br/>Validation & Quality Checks]:::etlProcess
        LOAD[Data Loading<br/>data_loader.py<br/>PostgreSQL Import]:::etlProcess
        QUERY[Query Execution<br/>query_runner.py<br/>Analytical Queries]:::etlProcess
    end

    %% Database Layer
    subgraph "Database Layer"
        POSTGRES[(PostgreSQL Database<br/>healthcare_db)]:::database
        
        subgraph "Database Tables"
            PATIENTS[patients<br/>150 records]:::database
            ENCOUNTERS[encounters<br/>291 records]:::database
            DIAGNOSES[diagnoses<br/>221 records]:::database
            MEDICATIONS[medications<br/>160 records]:::database
            PROCEDURES[procedures<br/>54 records]:::database
            OBSERVATIONS[observations<br/>886 records]:::database
        end
    end

    %% Queries
    subgraph "Analytical Queries"
        Q1[Query 1<br/>Average Age & Age Range<br/>patients table]:::query
        Q2[Query 2<br/>Patients per Physician<br/>encounters table]:::query
        Q3[Query 3<br/>Diagnoses by Age Group<br/>patients + diagnoses + medications]:::query
        Q4[Query 4<br/>Lab Value Trends<br/>patients + observations + encounters]:::query
        Q5[Query 5<br/>Procedure Outcomes<br/>patients + procedures + observations]:::query
    end

    %% Outputs
    subgraph "Outputs & Reports"
        RESULTS[Query Results<br/>output/query_results_*.txt]:::output
        QUALITY[Quality Reports<br/>data/quality_reports/]:::output
        LOGS[Log Files<br/>logs/]:::output
    end

    %% Infrastructure
    subgraph "Infrastructure"
        DOCKER[Docker Compose<br/>Container Orchestration]:::container
        PGADMIN[pgAdmin<br/>Database Management<br/>Optional]:::container
        VENV[Python Virtual Environment<br/>venv/]:::container
    end

    %% Data Flow Connections
    CSV --> CLEAN
    JSON --> CLEAN
    SQLITE --> CLEAN
    
    CLEAN --> LOAD
    LOAD --> POSTGRES
    
    POSTGRES --> PATIENTS
    POSTGRES --> ENCOUNTERS
    POSTGRES --> DIAGNOSES
    POSTGRES --> MEDICATIONS
    POSTGRES --> PROCEDURES
    POSTGRES --> OBSERVATIONS
    
    PATIENTS --> Q1
    ENCOUNTERS --> Q2
    PATIENTS --> Q3
    DIAGNOSES --> Q3
    MEDICATIONS --> Q3
    PATIENTS --> Q4
    OBSERVATIONS --> Q4
    ENCOUNTERS --> Q4
    PATIENTS --> Q5
    PROCEDURES --> Q5
    OBSERVATIONS --> Q5
    ENCOUNTERS --> Q5
    
    Q1 --> QUERY
    Q2 --> QUERY
    Q3 --> QUERY
    Q4 --> QUERY
    Q5 --> QUERY
    
    QUERY --> RESULTS
    CLEAN --> QUALITY
    LOAD --> QUALITY
    QUERY --> LOGS
    
    DOCKER --> POSTGRES
    DOCKER --> PGADMIN
    VENV --> CLEAN
    VENV --> LOAD
    VENV --> QUERY
```

## Data Flow Architecture

```mermaid
flowchart LR
    %% Styling
    classDef rawData fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#000
    classDef processing fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000
    classDef storage fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px,color:#000
    classDef analysis fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px,color:#000

    %% Raw Data Sources
    subgraph "Raw Data Sources"
        CSV_FILES[CSV Files<br/>• patients.csv<br/>• procedures.csv<br/>• observations.csv]:::rawData
        JSON_FILES[JSON Files<br/>• diagnoses.json<br/>• medications.json]:::rawData
        SQLITE_DB[SQLite Database<br/>• ehr_journeys_database.sqlite]:::rawData
    end

    %% Processing Steps
    subgraph "Data Processing"
        EXTRACT[Extract<br/>Read & Parse Files]:::processing
        TRANSFORM[Transform<br/>Clean & Validate]:::processing
        LOAD_DB[Load<br/>Import to PostgreSQL]:::processing
    end

    %% Storage
    subgraph "Data Storage"
        POSTGRES_DB[(PostgreSQL<br/>Normalized Schema)]:::storage
    end

    %% Analysis
    subgraph "Data Analysis"
        QUERIES[5 Cross-Dataset Queries<br/>• Demographic Analysis<br/>• Provider Statistics<br/>• Diagnosis Patterns<br/>• Lab Trends<br/>• Procedure Outcomes]:::analysis
    end

    %% Output
    subgraph "Output & Reporting"
        REPORTS[Reports & Logs<br/>• Query Results<br/>• Quality Reports<br/>• Performance Metrics]:::analysis
    end

    %% Flow
    CSV_FILES --> EXTRACT
    JSON_FILES --> EXTRACT
    SQLITE_DB --> EXTRACT
    EXTRACT --> TRANSFORM
    TRANSFORM --> LOAD_DB
    LOAD_DB --> POSTGRES_DB
    POSTGRES_DB --> QUERIES
    QUERIES --> REPORTS
```

## Component Architecture

```mermaid
graph TB
    %% Styling
    classDef config fill:#f1f8e9,stroke:#33691e,stroke-width:2px,color:#000
    classDef script fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#000
    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef infra fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#000

    %% Configuration
    subgraph "Configuration"
        ENV[.env File<br/>Database Credentials<br/>Environment Variables]:::config
        CONFIG_PY[config/database.py<br/>Database Connection<br/>Configuration]:::config
        LOGGING[config/logging_config.py<br/>Logging Setup]:::config
    end

    %% Scripts
    subgraph "ETL Scripts"
        CLEANING[scripts/data_cleaning.py<br/>Data Validation<br/>Quality Checks<br/>File Processing]:::script
        LOADING[scripts/data_loader.py<br/>Database Loading<br/>Error Handling<br/>Performance Monitoring]:::script
        QUERY_RUNNER[scripts/query_runner.py<br/>Query Execution<br/>Result Formatting<br/>Output Generation]:::script
    end

    %% Data Directories
    subgraph "Data Management"
        RAW[data/raw/<br/>Source Files]:::data
        PROCESSED[data/processed/<br/>Cleaned Data]:::data
        QUALITY_REPORTS[data/quality_reports/<br/>Quality Metrics]:::data
        OUTPUT[output/<br/>Query Results]:::data
        LOGS[logs/<br/>Application Logs]:::data
    end

    %% Infrastructure
    subgraph "Infrastructure"
        DOCKER_COMPOSE[docker-compose.yml<br/>Service Orchestration]:::infra
        DOCKERFILE[Dockerfile<br/>Python Environment]:::infra
        REQUIREMENTS[requirements.txt<br/>Dependencies]:::infra
        SCHEMA[sql/schema.sql<br/>Database Schema]:::infra
        QUERIES_SQL[sql/queries.sql<br/>Analytical Queries]:::infra
    end

    %% Dependencies
    ENV --> CONFIG_PY
    CONFIG_PY --> CLEANING
    CONFIG_PY --> LOADING
    CONFIG_PY --> QUERY_RUNNER
    LOGGING --> CLEANING
    LOGGING --> LOADING
    LOGGING --> QUERY_RUNNER
    
    RAW --> CLEANING
    CLEANING --> PROCESSED
    CLEANING --> QUALITY_REPORTS
    PROCESSED --> LOADING
    LOADING --> QUALITY_REPORTS
    LOADING --> LOGS
    QUERY_RUNNER --> OUTPUT
    QUERY_RUNNER --> LOGS
    
    DOCKER_COMPOSE --> DOCKERFILE
    DOCKERFILE --> REQUIREMENTS
    SCHEMA --> LOADING
    QUERIES_SQL --> QUERY_RUNNER
```

## Query Relationships Diagram

```mermaid
graph LR
    %% Styling
    classDef table fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px,color:#000
    classDef query fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000

    %% Database Tables
    subgraph "Database Tables"
        P[patients<br/>150 records]:::table
        E[encounters<br/>291 records]:::table
        D[diagnoses<br/>221 records]:::table
        M[medications<br/>160 records]:::table
        PR[procedures<br/>54 records]:::table
        O[observations<br/>886 records]:::table
    end

    %% Queries
    subgraph "Cross-Dataset Queries"
        Q1[Query 1<br/>Average Age & Range<br/>patients only]:::query
        Q2[Query 2<br/>Patients per Physician<br/>encounters only]:::query
        Q3[Query 3<br/>Diagnoses by Age + Meds<br/>patients + diagnoses + medications]:::query
        Q4[Query 4<br/>Lab Trends by Demographics<br/>patients + observations + encounters]:::query
        Q5[Query 5<br/>Procedure Outcomes<br/>patients + procedures + observations + encounters]:::query
    end

    %% Relationships
    P --> Q1
    E --> Q2
    P --> Q3
    D --> Q3
    M --> Q3
    P --> Q4
    O --> Q4
    E --> Q4
    P --> Q5
    PR --> Q5
    O --> Q5
    E --> Q5

    %% Table Relationships
    P -.->|patient_id| E
    P -.->|patient_id| D
    P -.->|patient_id| M
    P -.->|patient_id| PR
    P -.->|patient_id| O
    E -.->|encounter_id| D
    E -.->|encounter_id| M
    E -.->|encounter_id| PR
    E -.->|encounter_id| O
```

## Export Instructions

To export these diagrams in high resolution:

1. **Using Mermaid Live Editor:**
   - Copy each diagram code block to [Mermaid Live Editor](https://mermaid.live/)
   - Click "Download PNG" or "Download SVG" for high-resolution export

2. **Using VS Code:**
   - Install the "Mermaid Preview" extension
   - Open the .md file and use the preview
   - Right-click to save as PNG/SVG

3. **Using Command Line:**
   ```bash
   # Install mermaid-cli
   npm install -g @mermaid-js/mermaid-cli
   
   # Export to PNG
   mmdc -i architecture_diagram.md -o architecture.png -b transparent
   
   # Export to SVG
   mmdc -i architecture_diagram.md -o architecture.svg
   ```

4. **Using Online Tools:**
   - [Mermaid Chart](https://www.mermaidchart.com/)
   - [Draw.io](https://draw.io/) (import Mermaid code)

## Diagram Features

- **Color-coded components** for easy identification
- **Data flow arrows** showing ETL pipeline progression
- **Record counts** for each database table
- **Query relationships** showing which tables each query uses
- **Infrastructure components** including Docker and virtual environment
- **Output locations** for results, logs, and reports
- **Cross-dataset query visualization** showing the 5 analytical queries

The diagrams are designed to be:
- **High resolution** for professional documentation
- **Scalable** (SVG format recommended)
- **Clear and readable** with proper contrast
- **Comprehensive** covering all system components 