from typing import Dict, Any, List, Optional
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import logging
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from analyzer.analysis_storage_models import AnalysisResult, ExecutionLog, Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisStorageBase:
    def __init__(self, storage_path: str = "./analysis_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
         
        # Initialize SQLite database
        self.db_path = self.storage_path / "analysis.db"
        self.engine = create_engine(f"sqlite:///{self.db_path}")
         
        # Check if database exists and perform migration if needed
        if self.db_path.exists():
            self._migrate_database_schema()
         
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
         
        # Initialize vector embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_dim = 384  # Dimension of the embedding model
         
        # Initialize FAISS for vector storage
        self.faiss_index_path = self.storage_path / "faiss_index.bin"
        self.faiss_metadata_path = self.storage_path / "faiss_metadata.json"
        self.faiss_index = None
        self.faiss_id_to_record_id = {}  # Map FAISS IDs to SQLite record IDs
        self.record_id_to_faiss_id = {}  # Map SQLite record IDs to FAISS IDs
         
        # Load or create FAISS index
        self._initialize_faiss_index()
         
        # Load metadata and consistency check
        self._load_metadata_and_validate()
       
    def _migrate_database_schema(self):
        """Migrate existing database schema to add new profiling columns"""
        try:
            # Create a temporary engine to check existing schema
            temp_engine = create_engine(f"sqlite:///{self.db_path}")
            inspector = sa.inspect(temp_engine)
             
            # Check if analysis_results table exists
            if 'analysis_results' in inspector.get_table_names():
                columns = inspector.get_columns('analysis_results')
                column_names = {col['name'] for col in columns}
                 
                # List of new columns that need to be added
                new_columns = [
                    'scalene_cpu_data', 'scalene_memory_data', 'scalene_gpu_data', 'scalene_ai_suggestions',
                    'viztracer_call_data', 'viztracer_exception_data', 'viztracer_flow_data',
                    'scalene_timestamp', 'viztracer_timestamp',
                    'has_scalene_data', 'has_viztracer_data',
                    'scalene_coverage', 'viztracer_coverage',
                    'peak_memory_usage', 'cpu_hotspot_count', 'function_call_count', 'exception_count',
                    'scalene_execution_time', 'viztracer_execution_time',
                    'average_cpu_usage', 'average_memory_usage', 'gpu_utilization'
                ]
                 
                # Add missing columns
                with temp_engine.connect() as conn:
                    for column_name in new_columns:
                        if column_name not in column_names:
                            if column_name.endswith('_data') or column_name.endswith('_suggestions'):
                                # JSON columns
                                conn.execute(sa.text(f"ALTER TABLE analysis_results ADD COLUMN {column_name} JSON"))
                            elif column_name.endswith('_timestamp'):
                                # DateTime columns
                                conn.execute(sa.text(f"ALTER TABLE analysis_results ADD COLUMN {column_name} DATETIME"))
                            elif column_name in ['has_scalene_data', 'has_viztracer_data']:
                                # Integer columns (boolean flags)
                                conn.execute(sa.text(f"ALTER TABLE analysis_results ADD COLUMN {column_name} INTEGER DEFAULT 0"))
                            elif column_name.endswith('_coverage') or column_name.endswith('_usage') or column_name.endswith('_utilization'):
                                # Float columns
                                conn.execute(sa.text(f"ALTER TABLE analysis_results ADD COLUMN {column_name} FLOAT DEFAULT 0.0"))
                            elif column_name.endswith('_count') or column_name.endswith('_time'):
                                # Integer or Float columns for counts and times
                                if column_name.endswith('_count'):
                                    conn.execute(sa.text(f"ALTER TABLE analysis_results ADD COLUMN {column_name} INTEGER DEFAULT 0"))
                                else:
                                    conn.execute(sa.text(f"ALTER TABLE analysis_results ADD COLUMN {column_name} FLOAT DEFAULT 0.0"))
                             
                            logger.info(f"Added missing column: {column_name}")
                     
                    conn.commit()
                 
                logger.info("Database schema migration completed successfully")
             
        except Exception as e:
            logger.warning(f"Database migration failed: {e}")
            # Continue with existing schema, new columns will be added when creating new records
            logger.info("Continuing with existing schema, new columns will be added for new records")
       
    def _check_database_compatibility(self):
        """Check if existing database is compatible with current schema"""
        try:
            inspector = sa.inspect(self.engine)
            if 'analysis_results' in inspector.get_table_names():
                columns = inspector.get_columns('analysis_results')
                column_names = {col['name'] for col in columns}
                 
                # Check for critical columns that must exist
                required_columns = ['id', 'codebase_path', 'analysis_type', 'timestamp', 'summary']
                missing_critical = [col for col in required_columns if col not in column_names]
                 
                if missing_critical:
                    logger.error(f"Critical database columns missing: {missing_critical}")
                    return False
                 
                return True
            return False
             
        except Exception as e:
            logger.error(f"Database compatibility check failed: {e}")
            return False
       
    def _ensure_database_integrity(self):
        """Ensure database integrity after schema changes"""
        try:
            # Check if all required tables exist
            inspector = sa.inspect(self.engine)
            required_tables = ['analysis_results', 'execution_logs']
             
            for table_name in required_tables:
                if table_name not in inspector.get_table_names():
                    # Create missing tables
                    if table_name == 'analysis_results':
                        AnalysisResult.__table__.create(self.engine)
                    elif table_name == 'execution_logs':
                        ExecutionLog.__table__.create(self.engine)
                    logger.info(f"Created missing table: {table_name}")
             
            return True
             
        except Exception as e:
            logger.error(f"Database integrity check failed: {e}")
            return False
       
    def _get_database_version(self) -> int:
        """Get current database version"""
        try:
            # Check for version table
            if sa.inspect(self.engine).has_table('database_version'):
                result = self.session.execute(sa.text("SELECT version FROM database_version ORDER BY id DESC LIMIT 1"))
                return result.scalar() or 0
            return 0
        except Exception:
            return 0
       
    def _set_database_version(self, version: int):
        """Set database version"""
        try:
            # Create version table if it doesn't exist
            if not sa.inspect(self.engine).has_table('database_version'):
                self.session.execute(sa.text("""
                    CREATE TABLE database_version (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version INTEGER NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
             
            # Insert version record
            self.session.execute(sa.text("INSERT INTO database_version (version) VALUES (:version)"), 
                                {'version': version})
            self.session.commit()
        except Exception as e:
            logger.error(f"Failed to set database version: {e}")
            self.session.rollback()
       
    def _perform_schema_upgrade(self):
        """Perform comprehensive schema upgrade if needed"""
        try:
            current_version = self._get_database_version()
             
            # Version 1: Add profiling columns
            if current_version < 1:
                self._migrate_database_schema()
                self._set_database_version(1)
                logger.info("Database upgraded to version 1 with profiling support")
             
            return True
             
        except Exception as e:
            logger.error(f"Schema upgrade failed: {e}")
            return False
       
    def _validate_database_schema(self) -> bool:
        """Validate that database schema matches expected structure"""
        try:
            inspector = sa.inspect(self.engine)
             
            # Check analysis_results table
            if 'analysis_results' in inspector.get_table_names():
                columns = inspector.get_columns('analysis_results')
                column_types = {col['name']: col['type'] for col in columns}
                 
                # Verify critical column types
                expected_types = {
                    'id': 'INTEGER',
                    'codebase_path': 'VARCHAR',
                    'analysis_type': 'VARCHAR',
                    'timestamp': 'DATETIME',
                    'summary': 'TEXT'
                }
                 
                for col_name, expected_type in expected_types.items():
                    if col_name not in column_types:
                        logger.error(f"Missing critical column: {col_name}")
                        return False
                     
                    # Simple type checking (SQLite types are flexible)
                    actual_type = str(column_types[col_name]).upper()
                    if expected_type not in actual_type:
                        logger.warning(f"Column {col_name} type mismatch: expected {expected_type}, got {actual_type}")
                 
                return True
             
            return False
             
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False
       
    def _backup_database_before_migration(self) -> bool:
        """Create backup of database before migration"""
        try:
            backup_path = self.storage_path / f"analysis_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
             
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_path)
             
            logger.info(f"Database backup created at: {backup_path}")
            return True
             
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
       
    def _restore_database_from_backup(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            if not self.db_path.exists():
                import shutil
                shutil.copy2(backup_path, self.db_path)
                logger.info(f"Database restored from backup: {backup_path}")
                return True
            else:
                logger.error("Cannot restore: database file already exists")
                return False
                 
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
       
    def _get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        try:
            inspector = sa.inspect(self.engine)
            status = {
                'database_exists': self.db_path.exists(),
                'tables': inspector.get_table_names(),
                'version': self._get_database_version(),
                'compatible': self._check_database_compatibility()
            }
             
            if 'analysis_results' in status['tables']:
                columns = inspector.get_columns('analysis_results')
                status['column_count'] = len(columns)
                status['has_profiling_columns'] = any(
                    col['name'].startswith('scalene_') or col['name'].startswith('viztracer_')
                    for col in columns
                )
             
            return status
             
        except Exception as e:
            logger.error(f"Migration status check failed: {e}")
            return {'error': str(e)}