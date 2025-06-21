# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class ProjectTaskSample(models.Model):
    _name = 'project.task.sample'
    _description = 'Product Sample and Shipment Tracking'
    _order = 'create_date desc, id desc'
    _rec_name = 'reference'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Basic Information
    reference = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default='New',
        copy=False,
        tracking=True
    )
    
    tracking_type = fields.Selection([
        ('sample', 'Product Sample'),
        ('shipment', 'Final Shipment')
    ], string='Type', default='sample', required=True, tracking=True)
    
    task_id = fields.Many2one(
        'project.task',
        string='Related Task',
        required=True,
        ondelete='cascade',
        index=True,
        help='Task requesting this sample/shipment'
    )
    
    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier/Sender',
        required=True,
        domain=[('x_is_china_supplier', '=', True)],
        help='Company sending the sample/shipment',
        tracking=True
    )
    
    # Sample/Shipment Details
    sample_description = fields.Text(
        string='Description',
        required=True,
        help='Detailed description of the sample/shipment'
    )
    
    quantity = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        default=1.0,
        help='Number of units'
    )
    
    # Dates
    request_date = fields.Date(
        string='Request/Ship Date',
        default=fields.Date.today,
        required=True,
        tracking=True
    )
    
    expected_date = fields.Date(
        string='Expected Date',
        help='Expected arrival date'
    )
    
    received_date = fields.Date(
        string='Received Date',
        help='Actual receipt date at final destination',
        tracking=True
    )
    
    # Cost Information
    has_cost = fields.Boolean(
        string='Has Cost',
        help='Check if this sample/shipment requires payment'
    )
    
    sample_cost = fields.Monetary(
        string='Product Cost',
        currency_field='currency_id',
        help='Cost of the sample/product itself',
        tracking=True
    )
    
    shipping_cost = fields.Monetary(
        string='Shipping Cost',
        currency_field='currency_id',
        help='Cost of shipping'
    )
    
    total_cost = fields.Monetary(
        string='Total Cost',
        compute='_compute_total_cost',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    
    payment_state = fields.Selection([
        ('not_required', 'Not Required'),
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Payment Status', default='not_required', tracking=True)
    
    # Tracking Information
    current_location_id = fields.Many2one(
        'procurement.sample.location',
        string='Current Location',
        help='Current location of the sample/shipment',
        tracking=True
    )
    
    shipping_method_id = fields.Many2one(
        'procurement.shipping.method',
        string='Shipping Method',
        help='Method used to ship'
    )
    
    tracking_number = fields.Char(
        string='Tracking Number',
        help='Shipping tracking number'
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested/Shipped'),
        ('in_transit', 'In Transit'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)
    
    # Tracking Lines
    tracking_line_ids = fields.One2many(
        'project.task.sample.tracking',
        'sample_id',
        string='Tracking History'
    )
    
    # Attachments
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'sample_attachment_rel',
        'sample_id',
        'attachment_id',
        string='Attachments',
        help='Photos, documents, shipping labels, etc.'
    )
    
    # Notes
    notes = fields.Text(
        string='Notes',
        help='Additional notes'
    )
    
    # Related fields
    project_id = fields.Many2one(
        related='task_id.project_id',
        string='Project',
        store=True,
        readonly=True
    )
    
    product_display_name = fields.Char(
        related='task_id.x_product_display_name',
        string='Product',
        readonly=True
    )
    
    # Computed fields
    tracking_count = fields.Integer(
        string='Tracking Updates',
        compute='_compute_tracking_count',
        store=False
    )
    
    last_status_update = fields.Datetime(
        string='Last Update',
        compute='_compute_last_update',
        store=False
    )
    
    days_in_transit = fields.Integer(
        string='Days in Transit',
        compute='_compute_transit_days',
        store=False
    )
    
    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_overdue',
        store=False
    )
    
    # Display name based on type
    type_display = fields.Char(
        string='Type Display',
        compute='_compute_type_display',
        store=False
    )
    
    @api.depends('tracking_type')
    def _compute_type_display(self):
        """Compute display name based on type"""
        for record in self:
            if record.tracking_type == 'sample':
                record.type_display = 'Sample'
            else:
                record.type_display = 'Shipment'
    
    @api.depends('sample_cost', 'shipping_cost')
    def _compute_total_cost(self):
        """Calculate total cost"""
        for record in self:
            record.total_cost = (record.sample_cost or 0.0) + (record.shipping_cost or 0.0)
    
    @api.depends('tracking_line_ids')
    def _compute_tracking_count(self):
        """Count tracking updates"""
        for record in self:
            record.tracking_count = len(record.tracking_line_ids)
    
    @api.depends('tracking_line_ids.date')
    def _compute_last_update(self):
        """Get last tracking update date"""
        for record in self:
            if record.tracking_line_ids:
                record.last_status_update = max(record.tracking_line_ids.mapped('date'))
            else:
                record.last_status_update = record.create_date
    
    @api.depends('request_date', 'received_date', 'state')
    def _compute_transit_days(self):
        """Calculate days in transit"""
        for record in self:
            if record.request_date:
                if record.received_date:
                    delta = record.received_date - record.request_date
                    record.days_in_transit = delta.days
                elif record.state == 'in_transit':
                    delta = fields.Date.today() - record.request_date
                    record.days_in_transit = delta.days
                else:
                    record.days_in_transit = 0
            else:
                record.days_in_transit = 0
    
    @api.depends('expected_date', 'state')
    def _compute_overdue(self):
        """Check if sample/shipment is overdue"""
        today = fields.Date.today()
        for record in self:
            record.is_overdue = bool(
                record.expected_date and 
                record.expected_date < today and 
                record.state not in ['received', 'cancelled']
            )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generate reference on creation"""
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                # Use different sequence based on type
                if vals.get('tracking_type') == 'shipment':
                    vals['reference'] = self.env['ir.sequence'].next_by_code('project.task.shipment') or 'SHIP/New'
                else:
                    vals['reference'] = self.env['ir.sequence'].next_by_code('project.task.sample') or 'SAMPLE/New'
        return super().create(vals_list)
    
    @api.onchange('has_cost')
    def _onchange_has_cost(self):
        """Update payment state based on cost"""
        if self.has_cost:
            self.payment_state = 'pending'
        else:
            self.payment_state = 'not_required'
            self.sample_cost = 0.0
            self.shipping_cost = 0.0
    
    @api.onchange('tracking_type')
    def _onchange_tracking_type(self):
        """Update field labels based on type"""
        if self.tracking_type == 'shipment':
            # For final shipments, we might want different defaults
            pass
    
    def action_request(self):
        """Mark as requested/shipped"""
        self.ensure_one()
        self.state = 'requested'
        
        # Create initial tracking
        initial_status = self.env['procurement.sample.status'].search([('is_initial', '=', True)], limit=1)
        if initial_status:
            self.env['project.task.sample.tracking'].create({
                'sample_id': self.id,
                'status_id': initial_status.id,
                'date': fields.Datetime.now(),
                'notes': f'{self.type_display} requested from supplier' if self.tracking_type == 'sample' else 'Shipment initiated'
            })
        
        # Create activity for follow-up
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=f'Follow up on {self.type_display.lower()} request',
            date_deadline=fields.Date.today() + timedelta(days=7),
            user_id=self.env.user.id
        )
    
    def action_mark_in_transit(self):
        """Mark as in transit"""
        self.ensure_one()
        if not self.shipping_method_id:
            raise ValidationError(_('Please select a shipping method before marking as in transit.'))
        self.state = 'in_transit'
    
    def action_mark_received(self):
        """Mark as received"""
        self.ensure_one()
        self.write({
            'state': 'received',
            'received_date': fields.Date.today()
        })
        
        # Mark activities as done
        self.activity_ids.action_done()
    
    def action_cancel(self):
        """Cancel request"""
        self.ensure_one()
        self.state = 'cancelled'
        self.activity_ids.action_done()
    
    def action_mark_paid(self):
        """Mark as paid"""
        self.ensure_one()
        if not self.has_cost:
            raise ValidationError(_('This %s does not require payment.') % self.type_display.lower())
        self.payment_state = 'paid'
    
    def action_view_tracking(self):
        """View tracking history"""
        self.ensure_one()
        return {
            'name': _('%s Tracking History') % self.type_display,
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.sample.tracking',
            'view_mode': 'list,form',
            'domain': [('sample_id', '=', self.id)],
            'context': {'default_sample_id': self.id}
        }
    
    def action_print_tracking_report(self):
        """Print tracking report"""
        self.ensure_one()
        return self.env.ref('xportem_project_extension.report_sample_tracking').report_action(self)
    
    def action_add_tracking_update(self):
        """Quick add tracking update"""
        self.ensure_one()
        return {
            'name': _('Add Tracking Update'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.sample.tracking',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sample_id': self.id,
                'default_date': fields.Datetime.now(),
            }
        }
    
    @api.model
    def check_overdue_samples(self):
        """Cron method to check overdue samples/shipments"""
        overdue_records = self.search([
            ('expected_date', '<', fields.Date.today()),
            ('state', 'not in', ['received', 'cancelled'])
        ])
        
        for record in overdue_records:
            # Create activity for overdue items
            record.activity_schedule(
                'mail.mail_activity_data_warning',
                summary=f'{record.type_display} {record.reference} is overdue',
                date_deadline=fields.Date.today(),
                user_id=record.task_id.user_ids[:1].id or record.create_uid.id
            )
    
    def name_get(self):
        """Display name with reference and product"""
        result = []
        for record in self:
            name = f"{record.reference} - {record.product_display_name}"
            if record.tracking_type == 'shipment':
                name = f"[SHIP] {name}"
            result.append((record.id, name))
        return result