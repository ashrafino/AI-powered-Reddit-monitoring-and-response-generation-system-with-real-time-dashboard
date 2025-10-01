#!/usr/bin/env python3
"""
Database Schema Validation and Optimization Script

This script validates that all database tables exist with correct relationships
and constraints, and adds missing indexes for performance optimization.
"""

import sys
import logging
from sqlalchemy import create_engine, text, inspect, Index
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.models import *  # Import all models to register them

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseValidator:
    def __init__(self):
        self.engine = create_engine(settings.database_url, echo=False)
        self.inspector = inspect(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        
    def validate_schema(self):
        """Validate complete database schema"""
        logger.info("Starting database schema validation...")
        
        try:
            # Test database connection
            self._test_connection()
            
            # Validate tables exist
            self._validate_tables()
            
            # Validate relationships and constraints
            self._validate_relationships()
            
            # Add missing indexes
            self._add_missing_indexes()
            
            # Validate data integrity
            self._validate_data_integrity()
            
            logger.info("✅ Database schema validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database schema validation failed: {e}")
            return False
        finally:
            self.session.close()
    
    def _test_connection(self):
        """Test database connection"""
        logger.info("Testing database connection...")
        try:
            result = self.session.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("✅ Database connection successful")
        except SQLAlchemyError as e:
            raise Exception(f"Database connection failed: {e}")
    
    def _validate_tables(self):
        """Validate all required tables exist"""
        logger.info("Validating database tables...")
        
        expected_tables = {
            'clients', 'users', 'client_configs', 'matched_posts', 
            'ai_responses', 'analytics_events', 'performance_metrics', 
            'trend_analysis'
        }
        
        existing_tables = set(self.inspector.get_table_names())
        missing_tables = expected_tables - existing_tables
        
        if missing_tables:
            logger.info(f"Creating missing tables: {missing_tables}")
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Missing tables created")
        else:
            logger.info("✅ All required tables exist")
    
    def _validate_relationships(self):
        """Validate foreign key relationships and constraints"""
        logger.info("Validating table relationships and constraints...")
        
        # Check foreign key constraints
        constraints_to_check = [
            ('users', 'client_id', 'clients', 'id'),
            ('client_configs', 'client_id', 'clients', 'id'),
            ('matched_posts', 'client_id', 'clients', 'id'),
            ('ai_responses', 'post_id', 'matched_posts', 'id'),
            ('ai_responses', 'client_id', 'clients', 'id'),
            ('analytics_events', 'client_id', 'clients', 'id'),
            ('performance_metrics', 'client_id', 'clients', 'id'),
            ('trend_analysis', 'client_id', 'clients', 'id'),
        ]
        
        for table, fk_column, ref_table, ref_column in constraints_to_check:
            if table in self.inspector.get_table_names():
                fks = self.inspector.get_foreign_keys(table)
                fk_exists = any(
                    fk['constrained_columns'] == [fk_column] and 
                    fk['referred_table'] == ref_table and 
                    fk['referred_columns'] == [ref_column]
                    for fk in fks
                )
                if fk_exists:
                    logger.info(f"✅ Foreign key {table}.{fk_column} -> {ref_table}.{ref_column} exists")
                else:
                    logger.warning(f"⚠️  Foreign key {table}.{fk_column} -> {ref_table}.{ref_column} missing")
    
    def _add_missing_indexes(self):
        """Add missing indexes for performance optimization"""
        logger.info("Adding missing performance indexes...")
        
        # Define required indexes as specified in design document
        required_indexes = [
            # Client-scoped queries
            ('matched_posts', 'idx_matched_posts_client_created', ['client_id', 'created_at']),
            ('ai_responses', 'idx_ai_responses_client_created', ['client_id', 'created_at']),
            ('analytics_events', 'idx_analytics_client_date', ['client_id', 'created_at']),
            
            # Search and filtering
            ('matched_posts', 'idx_matched_posts_subreddit', ['subreddit']),
            ('matched_posts', 'idx_matched_posts_reviewed', ['client_id', 'reviewed']),
            ('ai_responses', 'idx_ai_responses_score', ['score']),
            
            # Analytics performance
            ('performance_metrics', 'idx_perf_client_date_period', ['client_id', 'date', 'period_type']),
            ('performance_metrics', 'idx_perf_keyword_date', ['keyword', 'date']),
            ('performance_metrics', 'idx_perf_subreddit_date', ['subreddit', 'date']),
            
            # Trend analysis
            ('trend_analysis', 'idx_trend_client_week', ['client_id', 'week_start']),
            ('trend_analysis', 'idx_trend_topic_week', ['topic', 'week_start']),
        ]
        
        existing_indexes = {}
        for table_name in self.inspector.get_table_names():
            existing_indexes[table_name] = [idx['name'] for idx in self.inspector.get_indexes(table_name)]
        
        indexes_added = 0
        for table_name, index_name, columns in required_indexes:
            if table_name in existing_indexes:
                if index_name not in existing_indexes[table_name]:
                    try:
                        # Create index using raw SQL for better control
                        columns_str = ', '.join(columns)
                        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
                        self.session.execute(text(sql))
                        self.session.commit()
                        logger.info(f"✅ Created index {index_name} on {table_name}({columns_str})")
                        indexes_added += 1
                    except SQLAlchemyError as e:
                        logger.warning(f"⚠️  Failed to create index {index_name}: {e}")
                else:
                    logger.info(f"✅ Index {index_name} already exists")
        
        if indexes_added > 0:
            logger.info(f"✅ Added {indexes_added} performance indexes")
        else:
            logger.info("✅ All required indexes already exist")
    
    def _validate_data_integrity(self):
        """Validate data integrity constraints"""
        logger.info("Validating data integrity...")
        
        try:
            # Check for orphaned records
            orphaned_queries = [
                ("users with invalid client_id", 
                 "SELECT COUNT(*) FROM users WHERE client_id IS NOT NULL AND client_id NOT IN (SELECT id FROM clients)"),
                ("client_configs with invalid client_id", 
                 "SELECT COUNT(*) FROM client_configs WHERE client_id NOT IN (SELECT id FROM clients)"),
                ("matched_posts with invalid client_id", 
                 "SELECT COUNT(*) FROM matched_posts WHERE client_id NOT IN (SELECT id FROM clients)"),
                ("ai_responses with invalid post_id", 
                 "SELECT COUNT(*) FROM ai_responses WHERE post_id NOT IN (SELECT id FROM matched_posts)"),
                ("ai_responses with invalid client_id", 
                 "SELECT COUNT(*) FROM ai_responses WHERE client_id NOT IN (SELECT id FROM clients)"),
            ]
            
            integrity_issues = 0
            for description, query in orphaned_queries:
                try:
                    result = self.session.execute(text(query)).scalar()
                    if result > 0:
                        logger.warning(f"⚠️  Found {result} {description}")
                        integrity_issues += 1
                    else:
                        logger.info(f"✅ No {description}")
                except SQLAlchemyError as e:
                    logger.warning(f"⚠️  Could not check {description}: {e}")
            
            if integrity_issues == 0:
                logger.info("✅ Data integrity validation passed")
            else:
                logger.warning(f"⚠️  Found {integrity_issues} data integrity issues")
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Data integrity validation failed: {e}")
    
    def get_schema_info(self):
        """Get detailed schema information"""
        logger.info("Gathering schema information...")
        
        schema_info = {
            'tables': {},
            'indexes': {},
            'constraints': {}
        }
        
        for table_name in self.inspector.get_table_names():
            # Table columns
            columns = self.inspector.get_columns(table_name)
            schema_info['tables'][table_name] = {
                'columns': len(columns),
                'column_details': [(col['name'], str(col['type']), col['nullable']) for col in columns]
            }
            
            # Indexes
            indexes = self.inspector.get_indexes(table_name)
            schema_info['indexes'][table_name] = [
                {'name': idx['name'], 'columns': idx['column_names'], 'unique': idx['unique']}
                for idx in indexes
            ]
            
            # Foreign keys
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            schema_info['constraints'][table_name] = [
                {
                    'name': fk['name'],
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns']
                }
                for fk in foreign_keys
            ]
        
        return schema_info

def main():
    """Main function to run schema validation"""
    validator = DatabaseValidator()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--info':
        # Print detailed schema information
        schema_info = validator.get_schema_info()
        
        print("\n=== DATABASE SCHEMA INFORMATION ===")
        for table_name, info in schema_info['tables'].items():
            print(f"\nTable: {table_name}")
            print(f"  Columns: {info['columns']}")
            for col_name, col_type, nullable in info['column_details']:
                null_str = "NULL" if nullable else "NOT NULL"
                print(f"    {col_name}: {col_type} {null_str}")
            
            if table_name in schema_info['indexes']:
                print(f"  Indexes:")
                for idx in schema_info['indexes'][table_name]:
                    unique_str = "UNIQUE" if idx['unique'] else ""
                    print(f"    {idx['name']}: {', '.join(idx['columns'])} {unique_str}")
            
            if table_name in schema_info['constraints']:
                print(f"  Foreign Keys:")
                for fk in schema_info['constraints'][table_name]:
                    print(f"    {fk['name']}: {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}")
    else:
        # Run validation
        success = validator.validate_schema()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()