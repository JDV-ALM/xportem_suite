# -*- coding: utf-8 -*-

import logging
from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Post-migration script to restore task relationships as Many2many
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Restore sample task relationships
    _logger.info("Restoring project.task.sample task relationships...")
    cr.execute("""
        INSERT INTO project_task_sample_task_rel (sample_id, task_id)
        SELECT sample_id, task_id
        FROM project_task_sample_migration
        WHERE sample_id IN (SELECT id FROM project_task_sample)
        AND task_id IN (SELECT id FROM project_task);
    """)
    
    sample_count = cr.rowcount
    _logger.info(f"Restored {sample_count} sample-task relationships")
    
    # Restore contract task relationships
    _logger.info("Restoring project.task.contract task relationships...")
    cr.execute("""
        INSERT INTO project_task_contract_task_rel (contract_id, task_id)
        SELECT contract_id, task_id
        FROM project_task_contract_migration
        WHERE contract_id IN (SELECT id FROM project_task_contract)
        AND task_id IN (SELECT id FROM project_task);
    """)
    
    contract_count = cr.rowcount
    _logger.info(f"Restored {contract_count} contract-task relationships")
    
    # Update the reverse relationships in project.task
    # The ORM will handle this automatically through the Many2many field
    
    # Clean up migration tables
    cr.execute("DROP TABLE IF EXISTS project_task_sample_migration;")
    cr.execute("DROP TABLE IF EXISTS project_task_contract_migration;")
    
    _logger.info("Post-migration completed successfully")
    
    # Force recomputation of computed fields
    Sample = env['project.task.sample']
    samples = Sample.search([])
    if samples:
        samples._compute_products_display()
        _logger.info(f"Recomputed products_display for {len(samples)} samples")
    
    Contract = env['project.task.contract']
    contracts = Contract.search([])
    if contracts:
        contracts._compute_products_display()
        _logger.info(f"Recomputed products_display for {len(contracts)} contracts")