# -*- coding: utf-8 -*-

import logging
from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration script to save existing task_id values before changing to Many2many
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Save sample task_id values
    _logger.info("Saving project.task.sample task_id values...")
    cr.execute("""
        CREATE TABLE IF NOT EXISTS project_task_sample_migration (
            sample_id INTEGER,
            task_id INTEGER
        );
        
        INSERT INTO project_task_sample_migration (sample_id, task_id)
        SELECT id, task_id
        FROM project_task_sample
        WHERE task_id IS NOT NULL;
    """)
    
    sample_count = cr.rowcount
    _logger.info(f"Saved {sample_count} sample-task relationships")
    
    # Save contract task_id values
    _logger.info("Saving project.task.contract task_id values...")
    cr.execute("""
        CREATE TABLE IF NOT EXISTS project_task_contract_migration (
            contract_id INTEGER,
            task_id INTEGER
        );
        
        INSERT INTO project_task_contract_migration (contract_id, task_id)
        SELECT id, task_id
        FROM project_task_contract
        WHERE task_id IS NOT NULL;
    """)
    
    contract_count = cr.rowcount
    _logger.info(f"Saved {contract_count} contract-task relationships")
    
    # Drop the old columns to avoid conflicts
    try:
        cr.execute("ALTER TABLE project_task_sample DROP COLUMN IF EXISTS task_id CASCADE;")
        _logger.info("Dropped task_id column from project_task_sample")
    except Exception as e:
        _logger.warning(f"Could not drop task_id from project_task_sample: {e}")
    
    try:
        cr.execute("ALTER TABLE project_task_contract DROP COLUMN IF EXISTS task_id CASCADE;")
        _logger.info("Dropped task_id column from project_task_contract")
    except Exception as e:
        _logger.warning(f"Could not drop task_id from project_task_contract: {e}")
    
    _logger.info("Pre-migration completed successfully")