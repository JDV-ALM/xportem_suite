# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProcurementShippingMethod(models.Model):
    _name = 'procurement.shipping.method'
    _description = 'Shipping Method Configuration'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Shipping Method',
        required=True,
        translate=True,
        help='Name of the shipping method (e.g., Air Freight, Sea Freight)'
    )
    
    code = fields.Char(
        string='Code',
        size=10,
        help='Short code (e.g., AIR, SEA)'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    shipping_type = fields.Selection([
        ('air', 'Air Freight'),
        ('sea', 'Sea Freight'),
        ('land', 'Land Transport'),
        ('courier', 'Courier Service'),
        ('other', 'Other')
    ], string='Type', default='air', required=True)
    
    estimated_days = fields.Integer(
        string='Estimated Transit Days',
        help='Average number of days for delivery'
    )
    
    is_express = fields.Boolean(
        string='Is Express',
        help='Mark if this is an express/urgent shipping method'
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help='Additional details about this shipping method'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Statistics
    sample_count = fields.Integer(
        string='Samples Shipped',
        compute='_compute_sample_count',
        store=False
    )
    
    @api.depends()
    def _compute_sample_count(self):
        """Count samples using this shipping method"""
        for method in self:
            # Will be implemented when sample model is created
            method.sample_count = 0
    
    def name_get(self):
        """Return name with code if available"""
        result = []
        for method in self:
            if method.code:
                name = f"[{method.code}] {method.name}"
            else:
                name = method.name
            result.append((method.id, name))
        return result