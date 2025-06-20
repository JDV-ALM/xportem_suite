# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    # Sample Management Fields
    sample_ids = fields.One2many(
        'project.task.sample',
        'task_id',
        string='Product Samples'
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
    
    # Contract Management Fields
    contract_ids = fields.One2many(
        'project.task.contract',
        'task_id',
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
    
    @api.depends('sample_ids', 'sample_ids.state')
    def _compute_sample_count(self):
        """Compute sample counts"""
        for task in self:
            task.sample_count = len(task.sample_ids)
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
        """View all samples for this task"""
        self.ensure_one()
        
        return {
            'name': self.env._('Product Samples - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.sample',
            'view_mode': 'list,form,kanban',
            'domain': [('task_id', '=', self.id)],
            'context': {
                'default_task_id': self.id,
                'default_supplier_id': self.x_selected_supplier_id.id if self.x_selected_supplier_id else False,
            }
        }
    
    def action_create_sample(self):
        """Create new sample request"""
        self.ensure_one()
        
        return {
            'name': self.env._('New Sample Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.sample',
            'view_mode': 'form',
            'context': {
                'default_task_id': self.id,
                'default_supplier_id': self.x_selected_supplier_id.id if self.x_selected_supplier_id else False,
                'default_sample_description': self.x_product_display_name or '',
            },
            'target': 'current',
        }
    
    def action_view_contracts(self):
        """View all contracts for this task"""
        self.ensure_one()
        
        return {
            'name': self.env._('Contracts & Invoices - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.contract',
            'view_mode': 'list,form',
            'domain': [('task_id', '=', self.id)],
            'context': {
                'default_task_id': self.id,
                'default_supplier_id': self.x_selected_supplier_id.id if self.x_selected_supplier_id else False,
            }
        }
    
    def action_create_contract(self):
        """Create new contract"""
        self.ensure_one()
        
        if not self.x_selected_supplier_id:
            raise ValidationError(
                self.env._('Please select a supplier before creating a contract.')
            )
        
        return {
            'name': self.env._('New Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.contract',
            'view_mode': 'form',
            'context': {
                'default_task_id': self.id,
                'default_supplier_id': self.x_selected_supplier_id.id,
                'default_purchase_order_id': self.x_purchase_order_id.id if self.x_purchase_order_id else False,
            },
            'target': 'current',
        }