# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class ProjectTaskSampleWizard(models.TransientModel):
    _name = 'project.task.sample.wizard'
    _description = 'Create Multiple Sample Requests'
    
    task_id = fields.Many2one(
        'project.task',
        string='Task',
        required=True,
        readonly=True
    )
    
    supplier_ids = fields.Many2many(
        'res.partner',
        string='Suppliers',
        required=True,
        domain=[('x_is_china_supplier', '=', True)],
        help='Select multiple suppliers to request samples from'
    )
    
    sample_description = fields.Text(
        string='Sample Description',
        required=True,
        help='This description will be used for all samples'
    )
    
    quantity = fields.Float(
        string='Quantity per Sample',
        default=1.0,
        required=True
    )
    
    has_cost = fields.Boolean(
        string='Samples Have Cost',
        help='Check if these samples require payment'
    )
    
    expected_date = fields.Date(
        string='Expected Date',
        help='Expected arrival date for all samples'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Additional notes for all samples'
    )
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        # Get task from context
        task_id = self._context.get('active_id')
        if task_id:
            task = self.env['project.task'].browse(task_id)
            res.update({
                'task_id': task_id,
                'sample_description': task.x_product_display_name or '',
                'supplier_ids': [(6, 0, task.x_potential_supplier_ids.ids)],
            })
        
        return res
    
    def action_create_samples(self):
        """Create sample requests for all selected suppliers"""
        self.ensure_one()
        
        if not self.supplier_ids:
            raise UserError('Please select at least one supplier.')
        
        Sample = self.env['project.task.sample']
        created_samples = Sample
        
        for supplier in self.supplier_ids:
            sample_vals = {
                'task_id': self.task_id.id,
                'supplier_id': supplier.id,
                'sample_description': self.sample_description,
                'quantity': self.quantity,
                'has_cost': self.has_cost,
                'expected_date': self.expected_date,
                'notes': self.notes,
                'request_date': fields.Date.today(),
            }
            created_samples |= Sample.create(sample_vals)
        
        # Return action to view created samples
        return {
            'name': 'Created Sample Requests',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.sample',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_samples.ids)],
            'context': {'search_default_group_supplier': 1},
        }