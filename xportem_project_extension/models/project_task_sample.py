# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class ProjectTaskSample(models.Model):
    _name = 'project.task.sample'
    _description = 'Product Sample Request'
    _order = 'create_date desc, id desc'
    _rec_name = 'reference'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add tracking
    
    # Basic Information
    reference = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default='New',
        copy=False,
        tracking=True
    )
    
    task_id = fields.Many2one(
        'project.task',
        string='Related Task',
        required=True,
        ondelete='cascade',
        index=True,
        help='Task requesting this sample'
    )
    
    supplier_id = fields.Many2one(
        'res.partner',
        string='Sample Provider',
        required=True,
        domain=[('x_is_china_supplier', '=', True)],
        help='Company sending the sample',
        tracking=True
    )
    
    # Sample Details
    sample_description = fields.Text(
        string='Sample Description',
        required=True,
        help='Detailed description of the sample'
    )
    
    quantity = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        default=1.0,
        help='Number of sample units'
    )
    
    # Dates
    request_date = fields.Date(
        string='Request Date',
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
        help='Check if this sample requires payment'
    )
    
    sample_cost = fields.Monetary(
        string='Sample Cost',
        currency_field='currency_id',
        help='Cost of the sample itself',
        tracking=True
    )
    
    shipping_cost = fields.Monetary(
        string='Shipping Cost',
        currency_field='currency_id',
        help='Cost of shipping the sample'
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
        help='Current location of the sample',
        tracking=True
    )
    
    shipping_method_id = fields.Many2one(
        'procurement.shipping.method',
        string='Shipping Method',
        help='Method used to ship the sample'
    )
    
    tracking_number = fields.Char(
        string='Tracking Number',
        help='Shipping tracking number'
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
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
        help='Additional notes about the sample'
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
    
    @api.depends('sample_cost', 'shipping_cost')
    def _compute_total_cost(self):
        """Calculate total cost"""
        for sample in self:
            sample.total_cost = (sample.sample_cost or 0.0) + (sample.shipping_cost or 0.0)
    
    @api.depends('tracking_line_ids')
    def _compute_tracking_count(self):
        """Count tracking updates"""
        for sample in self:
            sample.tracking_count = len(sample.tracking_line_ids)
    
    @api.depends('tracking_line_ids.date')
    def _compute_last_update(self):
        """Get last tracking update date"""
        for sample in self:
            if sample.tracking_line_ids:
                sample.last_status_update = max(sample.tracking_line_ids.mapped('date'))
            else:
                sample.last_status_update = sample.create_date
    
    @api.depends('request_date', 'received_date', 'state')
    def _compute_transit_days(self):
        """Calculate days in transit"""
        for sample in self:
            if sample.request_date:
                if sample.received_date:
                    delta = sample.received_date - sample.request_date
                    sample.days_in_transit = delta.days
                elif sample.state == 'in_transit':
                    delta = fields.Date.today() - sample.request_date
                    sample.days_in_transit = delta.days
                else:
                    sample.days_in_transit = 0
            else:
                sample.days_in_transit = 0
    
    @api.depends('expected_date', 'state')
    def _compute_overdue(self):
        """Check if sample is overdue"""
        today = fields.Date.today()
        for sample in self:
            sample.is_overdue = bool(
                sample.expected_date and 
                sample.expected_date < today and 
                sample.state not in ['received', 'cancelled']
            )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generate reference on creation"""
        for vals in vals_list:
            if vals.get('reference', 'New') == 'New':
                vals['reference'] = self.env['ir.sequence'].next_by_code('project.task.sample') or 'New'
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
    
    def action_request(self):
        """Mark sample as requested"""
        self.ensure_one()
        self.state = 'requested'
        
        # Create initial tracking
        initial_status = self.env['procurement.sample.status'].search([('is_initial', '=', True)], limit=1)
        if initial_status:
            self.env['project.task.sample.tracking'].create({
                'sample_id': self.id,
                'status_id': initial_status.id,
                'date': fields.Datetime.now(),
                'notes': 'Sample requested from supplier'
            })
        
        # EMAIL TEMPLATE COMMENTED OUT
        # Send email to supplier
        # template = self.env.ref('xportem_project_extension.email_template_sample_request', False)
        # if template:
        #     template.send_mail(self.id, force_send=True)
        
        # Create activity for follow-up
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary='Follow up on sample request',
            date_deadline=fields.Date.today() + timedelta(days=7),
            user_id=self.env.user.id
        )
    
    def action_mark_in_transit(self):
        """Mark sample as in transit"""
        self.ensure_one()
        if not self.shipping_method_id:
            raise ValidationError(_('Please select a shipping method before marking as in transit.'))
        self.state = 'in_transit'
    
    def action_mark_received(self):
        """Mark sample as received"""
        self.ensure_one()
        self.write({
            'state': 'received',
            'received_date': fields.Date.today()
        })
        
        # Mark activities as done
        self.activity_ids.action_done()
        
        # EMAIL TEMPLATE COMMENTED OUT
        # Send notification email
        # template = self.env.ref('xportem_project_extension.email_template_sample_received', False)
        # if template:
        #     template.send_mail(self.id, force_send=True)
    
    def action_cancel(self):
        """Cancel sample request"""
        self.ensure_one()
        self.state = 'cancelled'
        self.activity_ids.action_done()
    
    def action_mark_paid(self):
        """Mark sample as paid"""
        self.ensure_one()
        if not self.has_cost:
            raise ValidationError(_('This sample does not require payment.'))
        self.payment_state = 'paid'
    
    def action_view_tracking(self):
        """View tracking history"""
        self.ensure_one()
        return {
            'name': _('Sample Tracking History'),
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
        """Cron method to check overdue samples"""
        overdue_samples = self.search([
            ('expected_date', '<', fields.Date.today()),
            ('state', 'not in', ['received', 'cancelled'])
        ])
        
        for sample in overdue_samples:
            # Create activity for overdue samples
            sample.activity_schedule(
                'mail.mail_activity_data_warning',
                summary=f'Sample {sample.reference} is overdue',
                date_deadline=fields.Date.today(),
                user_id=sample.task_id.user_ids[:1].id or sample.create_uid.id
            )
    
    def name_get(self):
        """Display name with reference and product"""
        result = []
        for sample in self:
            name = f"{sample.reference} - {sample.product_display_name}"
            result.append((sample.id, name))
        return result