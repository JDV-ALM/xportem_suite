# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectTaskSampleTracking(models.Model):
    _name = 'project.task.sample.tracking'
    _description = 'Sample Tracking History'
    _order = 'date desc, id desc'
    _rec_name = 'status_id'
    
    sample_id = fields.Many2one(
        'project.task.sample',
        string='Sample',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    status_id = fields.Many2one(
        'procurement.sample.status',
        string='Status',
        required=True,
        help='Status of the sample at this point'
    )
    
    date = fields.Datetime(
        string='Date & Time',
        required=True,
        default=fields.Datetime.now,
        help='When this status was recorded'
    )
    
    location_id = fields.Many2one(
        'procurement.sample.location',
        string='Location',
        help='Where the sample is/was'
    )
    
    shipping_method_id = fields.Many2one(
        'procurement.shipping.method',
        string='Shipping Method',
        help='Shipping method used from this point'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Updated By',
        default=lambda self: self.env.user,
        readonly=True
    )
    
    notes = fields.Text(
        string='Notes',
        help='Additional information about this update'
    )
    
    # Related fields for easy access
    requires_location = fields.Boolean(
        related='status_id.requires_location',
        readonly=True
    )
    
    requires_shipping_method = fields.Boolean(
        related='status_id.requires_shipping_method',
        readonly=True
    )
    
    is_final = fields.Boolean(
        related='status_id.is_final',
        readonly=True
    )
    
    # Display fields
    sample_reference = fields.Char(
        related='sample_id.reference',
        string='Sample Reference',
        readonly=True
    )
    
    supplier_name = fields.Char(
        related='sample_id.supplier_id.name',
        string='Supplier',
        readonly=True
    )
    
    @api.constrains('location_id', 'status_id')
    def _check_location_requirement(self):
        """Validate location is provided when required"""
        for tracking in self:
            if tracking.requires_location and not tracking.location_id:
                raise ValidationError(
                    _('Location is required for status: %s') % tracking.status_id.name
                )
    
    @api.constrains('shipping_method_id', 'status_id')
    def _check_shipping_method_requirement(self):
        """Validate shipping method is provided when required"""
        for tracking in self:
            if tracking.requires_shipping_method and not tracking.shipping_method_id:
                raise ValidationError(
                    _('Shipping method is required for status: %s') % tracking.status_id.name
                )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Update sample current location on create"""
        trackings = super().create(vals_list)
        
        for tracking in trackings:
            # Update sample's current location if provided
            if tracking.location_id:
                tracking.sample_id.current_location_id = tracking.location_id
            
            # Update sample's shipping method if provided
            if tracking.shipping_method_id:
                tracking.sample_id.shipping_method_id = tracking.shipping_method_id
            
            # Update sample state if this is a final status
            if tracking.is_final:
                tracking.sample_id.state = 'received'
        
        return trackings
    
    def name_get(self):
        """Display name with date and status"""
        result = []
        for tracking in self:
            date_str = fields.Datetime.to_string(tracking.date)[:16]  # Remove seconds
            name = f"{date_str} - {tracking.status_id.name}"
            if tracking.location_id:
                name += f" @ {tracking.location_id.name}"
            result.append((tracking.id, name))
        return result