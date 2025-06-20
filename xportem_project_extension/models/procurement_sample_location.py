# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProcurementSampleLocation(models.Model):
    _name = 'procurement.sample.location'
    _description = 'Sample Location Configuration'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Location Name',
        required=True,
        translate=True,
        help='Name of the location (e.g., Broker Office, Final Destination)'
    )
    
    code = fields.Char(
        string='Code',
        size=10,
        help='Short code for the location'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order in the logistics chain'
    )
    
    location_type = fields.Selection([
        ('origin', 'Origin (Supplier)'),
        ('broker', 'Broker/Agent'),
        ('transit', 'In Transit'),
        ('customs', 'Customs'),
        ('destination', 'Final Destination'),
        ('warehouse', 'Warehouse'),
        ('other', 'Other')
    ], string='Location Type', default='other', required=True)
    
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        help='Country where this location is'
    )
    
    city = fields.Char(
        string='City',
        help='City name'
    )
    
    is_final_destination = fields.Boolean(
        string='Is Final Destination',
        help='Mark if this is typically the final destination'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Associated Partner',
        help='Partner managing this location (e.g., broker company)'
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help='Additional details about this location'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Statistics
    sample_count = fields.Integer(
        string='Samples at Location',
        compute='_compute_sample_count',
        store=False
    )
    
    @api.depends()
    def _compute_sample_count(self):
        """Count samples at this location"""
        for location in self:
            # Will be implemented when sample tracking model is created
            location.sample_count = 0
    
    def name_get(self):
        """Return name with location type"""
        result = []
        for location in self:
            type_name = dict(self._fields['location_type'].selection).get(location.location_type, '')
            if location.country_id:
                name = f"{location.name} ({type_name}) - {location.country_id.name}"
            else:
                name = f"{location.name} ({type_name})"
            result.append((location.id, name))
        return result