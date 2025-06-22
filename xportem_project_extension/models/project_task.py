# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    # Sample/Shipment Management Fields - UPDATED
    sample_ids = fields.Many2many(
        'project.task.sample',
        'project_task_sample_task_rel',
        'task_id',
        'sample_id',
        string='Samples & Shipments'
    )
    
    sample_count = fields.Integer(
        string='Sample Count',
        compute='_compute_sample_count',
        store=False
    )
    
    active_sample_count = fields.Integer(
        string='Active Samples',
        compute='_compute_sample_count',
        store=False
    )
    
    shipment_count = fields.Integer(
        string='Shipment Count',
        compute='_compute_sample_count',
        store=False
    )
    
    # Contract Management Fields - UPDATED
    contract_ids = fields.Many2many(
        'project.task.contract',
        'project_task_contract_task_rel',
        'task_id',
        'contract_id',
        string='Contracts & Invoices'
    )
    
    contract_count = fields.Integer(
        string='Contract Count',
        compute='_compute_contract_count',
        store=False
    )
    
    has_signed_contract = fields.Boolean(
        string='Has Signed Contract',
        compute='_compute_contract_status',
        store=False
    )
    
    has_invoice = fields.Boolean(
        string='Has Invoice',
        compute='_compute_contract_status',
        store=False
    )
    
    # Summary Fields
    total_sample_cost = fields.Monetary(
        string='Total Sample Cost',
        compute='_compute_sample_costs',
        store=False,
        currency_field='currency_id'
    )
    
    pending_sample_payments = fields.Integer(
        string='Pending Sample Payments',
        compute='_compute_sample_costs',
        store=False
    )
    
    @api.depends('sample_ids', 'sample_ids.state', 'sample_ids.tracking_type')
    def _compute_sample_count(self):
        """Compute sample and shipment counts"""
        for task in self:
            samples = task.sample_ids.filtered(lambda s: s.tracking_type == 'sample')
            shipments = task.sample_ids.filtered(lambda s: s.tracking_type == 'shipment')
            
            task.sample_count = len(samples)
            task.shipment_count = len(shipments)
            task.active_sample_count = len(task.sample_ids.filtered(
                lambda s: s.state not in ['received', 'cancelled']
            ))
    
    @api.depends('contract_ids')
    def _compute_contract_count(self):
        """Compute contract count"""
        for task in self:
            task.contract_count = len(task.contract_ids)
    
    @api.depends('contract_ids.state', 'contract_ids.has_invoice')
    def _compute_contract_status(self):
        """Compute contract and invoice status"""
        for task in self:
            signed_contracts = task.contract_ids.filtered(
                lambda c: c.state in ['signed', 'invoiced', 'completed']
            )
            task.has_signed_contract = bool(signed_contracts)
            task.has_invoice = any(task.contract_ids.mapped('has_invoice'))
    
    @api.depends('sample_ids.total_cost', 'sample_ids.payment_state')
    def _compute_sample_costs(self):
        """Compute sample cost totals"""
        for task in self:
            task.total_sample_cost = sum(task.sample_ids.mapped('total_cost'))
            task.pending_sample_payments = len(task.sample_ids.filtered(
                lambda s: s.payment_state == 'pending'
            ))
    
    # Action Methods
    def action_view_samples(self):
        """View all samples and shipments for this task"""
        self.ensure_one()
        
        return {
            'name': _('Samples & Shipments - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.sample',
            'view_mode': 'list,form,kanban',
            'domain': [('task_ids', 'in', self.id)],
            'context': {
                'default_task_ids': [(6, 0, [self.id])],
                'default_supplier_id': self.x_selected_supplier_id.id if self.x_selected_supplier_id else False,
                'search_default_group_type': 1,
            }
        }
    
    def action_create_sample(self):
        """Create new sample or shipment request - Opens wizard"""
        self.ensure_one()
        
        # Use the wizard for multiple suppliers
        return {
            'name': _('Create Sample/Shipment Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.sample.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_task_ids': [(6, 0, [self.id])],
                'default_sample_description': self.x_product_display_name or '',
                'default_supplier_ids': [(6, 0, self.x_potential_supplier_ids.ids)] if self.x_potential_supplier_ids else False,
            }
        }
    
    def action_view_contracts(self):
        """View all contracts for this task"""
        self.ensure_one()
        
        return {
            'name': _('Contracts & Invoices - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.contract',
            'view_mode': 'list,form',
            'domain': [('task_ids', 'in', self.id)],
            'context': {
                'default_task_ids': [(6, 0, [self.id])],
                'default_supplier_id': self.x_selected_supplier_id.id if self.x_selected_supplier_id else False,
            }
        }
    
    def action_create_contract(self):
        """Create new contract"""
        self.ensure_one()
        
        # Get default supplier - either selected or first potential
        default_supplier = self.x_selected_supplier_id
        if not default_supplier and self.x_potential_supplier_ids:
            default_supplier = self.x_potential_supplier_ids[0]
        
        return {
            'name': _('New Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.contract',
            'view_mode': 'form',
            'context': {
                'default_task_ids': [(6, 0, [self.id])],
                'default_supplier_id': default_supplier.id if default_supplier else False,
                'default_purchase_order_id': self.x_purchase_order_id.id if self.x_purchase_order_id else False,
            },
            'target': 'current',
        }