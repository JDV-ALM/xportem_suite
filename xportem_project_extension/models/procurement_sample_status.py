# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProcurementSampleStatus(models.Model):
    _name = 'procurement.sample.status'
    _description = 'Sample Status Configuration'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Status Name',
        required=True,
        translate=True,
        help='Name of the sample status (e.g., Requested, Sent by Supplier, etc.)'
    )
    
    code = fields.Char(
        string='Code',
        size=20,
        help='Short code for the status'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of status in the process'
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help='Detailed description of what this status means'
    )
    
    is_initial = fields.Boolean(
        string='Is Initial Status',
        help='Mark if this is the initial status for new samples'
    )
    
    is_final = fields.Boolean(
        string='Is Final Status',
        help='Mark if this is a final status (sample received or cancelled)'
    )
    
    requires_location = fields.Boolean(
        string='Requires Location',
        help='Check if this status requires specifying a location'
    )
    
    requires_shipping_method = fields.Boolean(
        string='Requires Shipping Method',
        help='Check if this status requires specifying shipping method'
    )
    
    color = fields.Integer(
        string='Color Index',
        default=0,
        help='Color for kanban and status display'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Statistics
    sample_count = fields.Integer(
        string='Sample Count',
        compute='_compute_sample_count',
        store=False
    )
    
    @api.depends()
    def _compute_sample_count(self):
        """Count samples using this status"""
        for status in self:
            # Will be implemented when sample tracking model is created
            status.sample_count = 0
    
    @api.constrains('is_initial')
    def _check_single_initial(self):
        """Ensure only one initial status exists"""
        if self.filtered('is_initial'):
            initial_count = self.search_count([
                ('is_initial', '=', True),
                ('id', 'not in', self.ids)
            ])
            if initial_count > 0:
                raise ValidationError(
                    self.env._('Only one status can be marked as initial.')
                )
    
    def name_get(self):
        """Return name with sequence"""
        result = []
        for status in self:
            name = f"[{status.sequence}] {status.name}"
            if status.code:
                name = f"{status.code} - {name}"
            result.append((status.id, name))
        return result