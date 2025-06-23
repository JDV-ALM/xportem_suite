# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectTaskContract(models.Model):
    _name = 'project.task.contract'
    _description = 'Task Purchase Contract and Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'contract_reference'
    
    # Basic Information
    # CHANGED: Many2one to Many2many
    task_ids = fields.Many2many(
        'project.task',
        'project_task_contract_task_rel',
        'contract_id',
        'task_id',
        string='Related Tasks',
        required=True,
        help='Tasks for this contract'
    )
    
    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        required=True,
        domain=[('x_is_china_supplier', '=', True)],
        help='Selected supplier for this purchase',
        tracking=True
    )
    
    # Contract Information
    contract_reference = fields.Char(
        string='Contract Reference',
        required=True,
        help='Contract number or reference',
        tracking=True
    )
    
    contract_date = fields.Date(
        string='Contract Date',
        required=True,
        default=fields.Date.today,
        help='Date when contract was signed',
        tracking=True
    )
    
    contract_file = fields.Binary(
        string='Contract File',
        help='Signed contract document'
    )
    
    contract_filename = fields.Char(
        string='Contract Filename'
    )
    
    # Financial Information
    contract_amount = fields.Monetary(
        string='Contract Amount',
        currency_field='currency_id',
        required=True,
        help='Total contract value',
        tracking=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    payment_terms = fields.Text(
        string='Payment Terms',
        help='Payment conditions agreed in the contract'
    )
    
    # Invoice Information
    has_invoice = fields.Boolean(
        string='Has Invoice',
        help='Check when invoice is received',
        tracking=True
    )
    
    invoice_number = fields.Char(
        string='Invoice Number',
        help='Supplier invoice number'
    )
    
    invoice_date = fields.Date(
        string='Invoice Date',
        help='Date on the invoice'
    )
    
    invoice_file = fields.Binary(
        string='Invoice File',
        help='Invoice document'
    )
    
    invoice_filename = fields.Char(
        string='Invoice Filename'
    )
    
    invoice_amount = fields.Monetary(
        string='Invoice Amount',
        currency_field='currency_id',
        help='Amount on the invoice'
    )
    
    # Purchase Order Link (if available)
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
        help='Related purchase order in Odoo'
    )
    
    # Delivery Information
    delivery_terms = fields.Char(
        string='Delivery Terms',
        help='INCOTERMS or delivery conditions'
    )
    
    expected_delivery_date = fields.Date(
        string='Expected Delivery',
        help='Expected delivery date per contract'
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('signed', 'Contract Signed'),
        ('invoiced', 'Invoiced'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Related fields - UPDATED for Many2many
    project_ids = fields.Many2many(
        'project.project',
        string='Projects',
        compute='_compute_project_ids',
        store=False
    )
    
    # NEW: Computed field to show all products
    products_display = fields.Char(
        string='Products',
        compute='_compute_products_display',
        store=False
    )
    
    # Additional Documents
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'contract_attachment_rel',
        'contract_id',
        'attachment_id',
        string='Additional Documents',
        help='Other related documents (specs, certificates, etc.)'
    )
    
    # Notes
    notes = fields.Text(
        string='Notes',
        help='Additional notes about this contract'
    )
    
    @api.depends('task_ids', 'task_ids.project_id')
    def _compute_project_ids(self):
        """Compute projects from tasks"""
        for contract in self:
            contract.project_ids = contract.task_ids.mapped('project_id')
    
    @api.depends('task_ids.x_product_display_name')
    def _compute_products_display(self):
        """Compute display of all products from tasks"""
        for contract in self:
            products = contract.task_ids.mapped('x_product_display_name')
            products = [p for p in products if p]  # Filter empty values
            if products:
                if len(products) <= 3:
                    contract.products_display = ', '.join(products)
                else:
                    contract.products_display = ', '.join(products[:3]) + f' (+{len(products) - 3} more)'
            else:
                contract.products_display = ''
    
    @api.constrains('invoice_amount', 'contract_amount')
    def _check_invoice_amount(self):
        """Warning if invoice amount differs from contract"""
        for contract in self:
            if contract.has_invoice and contract.invoice_amount and contract.contract_amount:
                if abs(contract.invoice_amount - contract.contract_amount) > 0.01:
                    # Just a warning, not a hard constraint
                    pass
    
    @api.onchange('has_invoice')
    def _onchange_has_invoice(self):
        """Update state when invoice is marked"""
        if self.has_invoice and self.state == 'signed':
            self.state = 'invoiced'
        elif not self.has_invoice and self.state == 'invoiced':
            self.state = 'signed'
    
    @api.model_create_multi
    def create(self, vals_list):
        """Set supplier from tasks if not provided"""
        for vals in vals_list:
            if 'supplier_id' not in vals and vals.get('task_ids'):
                # Get task_ids from the many2many command
                task_ids = []
                if isinstance(vals['task_ids'][0], (list, tuple)) and vals['task_ids'][0][0] == 6:
                    task_ids = vals['task_ids'][0][2]
                elif isinstance(vals['task_ids'][0], (list, tuple)) and vals['task_ids'][0][0] == 4:
                    # Handle [(4, id), ...] format
                    task_ids = [cmd[1] for cmd in vals['task_ids'] if cmd[0] == 4]
                
                if task_ids:
                    tasks = self.env['project.task'].browse(task_ids)
                    # Get the most common selected supplier from tasks
                    suppliers = tasks.mapped('x_selected_supplier_id')
                    if suppliers:
                        # Use the most frequent supplier
                        supplier_counts = {}
                        for supplier in suppliers:
                            supplier_counts[supplier.id] = supplier_counts.get(supplier.id, 0) + 1
                        most_common = max(supplier_counts, key=supplier_counts.get)
                        vals['supplier_id'] = most_common
                        
        return super().create(vals_list)
    
    def action_sign_contract(self):
        """Mark contract as signed"""
        self.ensure_one()
        if not self.contract_file:
            raise ValidationError(_('Please upload the contract file before marking as signed.'))
        self.state = 'signed'
    
    def action_complete(self):
        """Mark contract as completed"""
        self.ensure_one()
        self.state = 'completed'
    
    def action_cancel(self):
        """Cancel contract"""
        self.ensure_one()
        self.state = 'cancelled'
    
    def action_preview_contract(self):
        """Preview contract PDF"""
        self.ensure_one()
        if not self.contract_file:
            raise ValidationError(_('No contract file to preview.'))
        
        # Create attachment if it doesn't exist
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('res_field', '=', 'contract_file')
        ], limit=1)
        
        if not attachment:
            attachment = self.env['ir.attachment'].create({
                'name': self.contract_filename or 'Contract.pdf',
                'type': 'binary',
                'datas': self.contract_file,
                'res_model': self._name,
                'res_id': self.id,
                'res_field': 'contract_file',
                'mimetype': 'application/pdf',
            })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=false',
            'target': 'new',
        }
    
    def action_preview_invoice(self):
        """Preview invoice PDF"""
        self.ensure_one()
        if not self.invoice_file:
            raise ValidationError(_('No invoice file to preview.'))
        
        # Create attachment if it doesn't exist
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('res_field', '=', 'invoice_file')
        ], limit=1)
        
        if not attachment:
            attachment = self.env['ir.attachment'].create({
                'name': self.invoice_filename or 'Invoice.pdf',
                'type': 'binary',
                'datas': self.invoice_file,
                'res_model': self._name,
                'res_id': self.id,
                'res_field': 'invoice_file',
                'mimetype': 'application/pdf',
            })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=false',
            'target': 'new',
        }
    
    def unlink(self):
        """Override to restrict deletion to administrators only"""
        if not self.env.user.has_group('base.group_system'):
            raise ValidationError(_('Only administrators can delete contracts.'))
        return super().unlink()
    
    def action_delete_contract(self):
        """Delete contract - only for administrators"""
        self.ensure_one()
        if not self.env.user.has_group('base.group_system'):
            raise ValidationError(_('Only administrators can delete contracts.'))
        
        # Confirm dialog will be shown by the client
        return {
            'type': 'ir.actions.act_window_close',
            'infos': {'force_reload': True},
        }
    
    def name_get(self):
        """Display name with reference and supplier"""
        result = []
        for contract in self:
            # Show products info if multiple
            if len(contract.task_ids) > 1:
                name = f"{contract.contract_reference} - {contract.supplier_id.name} ({len(contract.task_ids)} products)"
            else:
                name = f"{contract.contract_reference} - {contract.supplier_id.name}"
            result.append((contract.id, name))
        return result