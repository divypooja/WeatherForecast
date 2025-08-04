#!/usr/bin/env python3
"""
Migration script to add process transformation fields to BOM processes
Adds input_product_id, output_product_id, input_quantity, output_quantity, and transformation_type fields
"""

from app import app, db
from models import BOMProcess
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def migrate_bom_process_transformation():
    """Add transformation tracking fields to BOM processes table"""
    with app.app_context():
        logging.info("Starting BOM Process Transformation migration...")
        
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('bom_processes')]
            
            new_columns = [
                'input_product_id',
                'output_product_id',
                'input_quantity',
                'output_quantity',
                'transformation_type'
            ]
            
            # Add missing columns
            for column in new_columns:
                if column not in columns:
                    try:
                        if column == 'input_product_id':
                            db.session.execute(text(f"ALTER TABLE bom_processes ADD COLUMN {column} INTEGER REFERENCES items(id)"))
                            logging.info(f"Added column: {column}")
                        elif column == 'output_product_id':
                            db.session.execute(text(f"ALTER TABLE bom_processes ADD COLUMN {column} INTEGER REFERENCES items(id)"))
                            logging.info(f"Added column: {column}")
                        elif column == 'input_quantity':
                            db.session.execute(text(f"ALTER TABLE bom_processes ADD COLUMN {column} REAL DEFAULT 1.0"))
                            logging.info(f"Added column: {column}")
                        elif column == 'output_quantity':
                            db.session.execute(text(f"ALTER TABLE bom_processes ADD COLUMN {column} REAL DEFAULT 1.0"))
                            logging.info(f"Added column: {column}")
                        elif column == 'transformation_type':
                            db.session.execute(text(f"ALTER TABLE bom_processes ADD COLUMN {column} VARCHAR(50) DEFAULT 'modify'"))
                            logging.info(f"Added column: {column}")
                        db.session.commit()
                    except Exception as e:
                        logging.warning(f"Could not add column {column}: {e}")
                        db.session.rollback()
                else:
                    logging.info(f"Column {column} already exists")
            
            # Commit the changes
            db.session.commit()
            logging.info("Migration completed successfully!")
            
            # Update existing processes with default transformation data
            processes = BOMProcess.query.all()
            for process in processes:
                if not process.transformation_type:
                    process.transformation_type = 'modify'
                if not process.input_quantity:
                    process.input_quantity = 1.0
                if not process.output_quantity:
                    process.output_quantity = 1.0
            
            db.session.commit()
            logging.info(f"Updated {len(processes)} existing BOM processes with default transformation data")
            
        except Exception as e:
            logging.error(f"Migration failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    migrate_bom_process_transformation()