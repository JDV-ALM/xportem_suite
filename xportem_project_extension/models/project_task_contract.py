# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProjectTaskContract(models.Model):
    _name = 'project.task.contract'
    _description = 'Task Purchase Contract and Invoice'
    _order = 'create_date desc'
    _rec_name = 'contract_reference'
    
    # Basic Information
    task_id = fields.Many2one(
        'project.task',
        string='Related Task',
        required=True,
        ondelete='cascade',
        help='Task for this contract'
    )
    
    supplier_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        required=True,
        domain=[('x_is_china_supplier', '=', True)],
        help='Selected supplier for this purchase'
    )
    
    # Contract Information
    contract_reference = fields.Char(
        string='Contract Reference',
        required=True,
        help='Contract number or reference'
    )
    
    contract_date = fields.Date(
        string='Contract Date',
        required=True,
        default=fields.Date.today,
        help='Date when contract was signed'
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
        help='Total contract value'
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
        help='Check when invoice is received'
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
    
    selected_supplier_id = fields.Many2one(
        related='task_id.x_selected_supplier_id',
        string='Task Selected Supplier',
        readonly=True
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
    
    @api.constrains('supplier_id', 'selected_supplier_id')
    def _check_supplier_consistency(self):
        """Ensure contract supplier matches task selected supplier"""
        for contract in self:
            if contract.selected_supplier_id and contract.supplier_id != contract.selected_supplier_id:
                raise ValidationError(
                    self.env._('Contract supplier must match the selected supplier in the task.')
                )
    
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
        """Set supplier from task if not provided"""
        for vals in vals_list:
            if 'supplier_id' not in vals and vals.get('task_id'):
                task = self.env['project.task'].browse(vals['task_id'])
                if task.x_selected_supplier_id:
                    vals['supplier_id'] = task.x_selected_supplier_id.id
        return super().create(vals_list)
    
    def action_sign_contract(self):
        """Mark contract as signed"""
        self.ensure_one()
        if not self.contract_file:
            raise ValidationError(self.env._('Please upload the contract file before marking as signed.'))
        self.state = 'signed'
    
    def action_complete(self):
        """Mark contract as completed"""
        self.ensure_one()
        self.state = 'completed'
    
    def action_cancel(self):
        """Cancel contract"""
        self.ensure_one()
        self.state = 'cancelled'
    
    def name_get(self):
        """Display name with reference and supplier"""
        result = []
        for contract in self:
            name = f"{contract.contract_reference} - {contract.supplier_id.name}"
            result.append((contract.id, name))
        return result