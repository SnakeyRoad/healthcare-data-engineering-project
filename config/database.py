"""
Healthcare Data Engineering Project - Database Configuration
Cross-platform database connectivity for Linux and Windows environments
"""

import os
import logging
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.database = os.getenv('POSTGRES_DB', 'healthcare_db')
        self.username = os.getenv('POSTGRES_USER', 'healthcare_admin')
        self.password = os.getenv('POSTGRES_PASSWORD', 'secure_password_2024')
        
        # SQLAlchemy configuration
        self.database_url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        
        # Connection pool settings
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '5'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '10'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        
    def get_engine(self):
        """Create SQLAlchemy engine with connection pooling"""
        return create_engine(
            self.database_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            echo=os.getenv('SQL_ECHO', 'False').lower() == 'true',
            future=True
        )
    
    def get_session_factory(self):
        """Create SQLAlchemy session factory"""
        engine = self.get_engine()
        return sessionmaker(bind=engine, autocommit=False, autoflush=False)
    
    def get_connection(self):
        """Get raw psycopg2 connection for direct SQL operations"""
        try:
            connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                cursor_factory=RealDictCursor
            )
            connection.autocommit = False
            return connection
        except psycopg2.Error as e:
            logging.error(f"Database connection failed: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    # RealDictCursor returns a dict-like object, so we need to access by column name
                    return result['?column?'] == 1
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False
    
    def execute_schema_file(self, schema_file_path: str) -> bool:
        """Execute SQL schema file"""
        try:
            with open(schema_file_path, 'r', encoding='utf-8') as file:
                schema_sql = file.read()
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
                    conn.commit()
                    logging.info(f"Schema file {schema_file_path} executed successfully")
                    return True
        except Exception as e:
            logging.error(f"Schema execution failed: {e}")
            return False

class DatabaseManager:
    """High-level database operations manager"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.engine = self.config.get_engine()
        self.SessionLocal = self.config.get_session_factory()
    
    def get_session(self):
        """Get database session with context manager support"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Optional[dict] = None) -> list:
        """Execute query and return results"""
        try:
            with self.config.get_connection() as conn:
                with conn.cursor() as cur:
                    if params:
                        cur.execute(query, params)
                    else:
                        cur.execute(query)
                    
                    if cur.description:  # Query returns results
                        rows = cur.fetchall()
                        # RealDictCursor already returns dict-like objects, so convert to regular dicts
                        return [dict(row) for row in rows]
                    else:  # Query doesn't return results (INSERT, UPDATE, DELETE)
                        conn.commit()
                        return []
        except Exception as e:
            logging.error(f"Query execution failed: {e}")
            raise
    
    def execute_file(self, file_path: str) -> bool:
        """Execute SQL file"""
        return self.config.execute_schema_file(file_path)
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if table exists in database"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
        """
        result = self.execute_query(query, {'table_name': table_name})
        return result[0]['exists'] if result else False
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get row count for a table"""
        if not self.check_table_exists(table_name):
            return 0
        
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_database_stats(self) -> dict:
        """Get comprehensive database statistics"""
        stats = {}
        
        # Get all table names
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        """
        
        tables = self.execute_query(tables_query)
        
        for table in tables:
            table_name = table['table_name']
            stats[table_name] = {
                'row_count': self.get_table_row_count(table_name),
                'exists': True
            }
        
        return stats
    
    def verify_referential_integrity(self) -> dict:
        """Check referential integrity across tables"""
        integrity_query = "SELECT * FROM check_referential_integrity();"
        try:
            results = self.execute_query(integrity_query)
            return {row['table_name']: row['issue_count'] for row in results}
        except Exception as e:
            logging.error(f"Referential integrity check failed: {e}")
            return {}

# Global database manager instance
db_manager = DatabaseManager()

def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    return db_manager

def init_database() -> bool:
    """Initialize database with schema"""
    try:
        # Test connection first
        if not db_manager.config.test_connection():
            logging.error("Database connection test failed")
            return False
        
        # Execute schema if needed
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'schema.sql')
        if os.path.exists(schema_path):
            success = db_manager.execute_file(schema_path)
            if success:
                logging.info("Database initialized successfully")
                return True
        
        logging.error("Schema file not found")
        return False
        
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    # Test database connection and initialization
    logging.basicConfig(level=logging.INFO)
    
    print("Testing database connection...")
    if db_manager.config.test_connection():
        print("Database connection successful")
        
        print("\nGetting database statistics...")
        stats = db_manager.get_database_stats()
        for table, info in stats.items():
            print(f"  {table}: {info['row_count']} rows")
        
        print("\nChecking referential integrity...")
        integrity = db_manager.verify_referential_integrity()
        for table, issues in integrity.items():
            if issues > 0:
                print(f"{table}: {issues} integrity issues")
            else:
                print(f"{table}: No integrity issues")
    else:
        print("Database connection failed")
