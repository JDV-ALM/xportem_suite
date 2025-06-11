# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProjectTaskQuotationLine(models.Model):
    _name = 'project.task.quotation.line'
    _description = 'Línea de Cotización de Tarea'
    _order = 'task_id, supplier_id, sequence'
    _rec_name = 'product_name'
    
    # ===== Basic Fields =====
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de las líneas'
    )
    
    task_id = fields.Many2one(
        'project.task',
        string='Tarea',
        required=True,
        ondelete='cascade',
        index=True,
        help='Tarea de procura relacionada'
    )
    
    supplier_id = fields.Many2one(
        'res.partner',
        string='Proveedor',
        required=True,
        domain=[('x_is_china_supplier', '=', True)],
        help='Proveedor que cotiza'
    )
    
    # ===== Product Information =====
    product_name = fields.Char(
        string='Producto Cotizado',
        required=True,
        help='Nombre del producto según el proveedor'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción detallada del producto cotizado'
    )
    
    # ===== Pricing Fields =====
    price_unit = fields.Float(
        string='Precio Unitario',
        digits='Product Price',
        required=True,
        help='Precio por unidad'
    )
    
    quantity = fields.Float(
        string='Cantidad',
        digits='Product Unit of Measure',
        required=True,
        default=1.0,
        help='Cantidad cotizada'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help='Moneda de la cotización'
    )
    
    price_total = fields.Monetary(
        string='Total',
        compute='_compute_price_total',
        store=True,
        currency_field='currency_id',
        help='Precio total de la línea'
    )
    
    # ===== Delivery Terms =====
    delivery_term = fields.Selection([
        ('exw', 'EXW - Ex Works'),
        ('fob', 'FOB - Free On Board'),
        ('cif', 'CIF - Cost, Insurance & Freight'),
        ('cfr', 'CFR - Cost & Freight'),
        ('cpt', 'CPT - Carriage Paid To'),
        ('cip', 'CIP - Carriage & Insurance Paid To'),
        ('dat', 'DAT - Delivered At Terminal'),
        ('dap', 'DAP - Delivered At Place'),
        ('ddp', 'DDP - Delivered Duty Paid'),
        ('fas', 'FAS - Free Alongside Ship'),
        ('fca', 'FCA - Free Carrier'),
    ], string='Término de Entrega', default='fob')
    
    lead_time = fields.Integer(
        string='Tiempo de Entrega (días)',
        help='Días de producción y entrega'
    )
    
    # ===== Additional Information =====
    payment_terms = fields.Char(
        string='Términos de Pago',
        help='Condiciones de pago del proveedor'
    )
    
    minimum_order_qty = fields.Float(
        string='MOQ',
        digits='Product Unit of Measure',
        help='Cantidad mínima de orden'
    )
    
    validity_date = fields.Date(
        string='Válido Hasta',
        help='Fecha de validez de la cotización'
    )
    
    # ===== File Attachments =====
    quotation_file = fields.Binary(
        string='Archivo de Cotización',
        help='PDF o archivo de cotización del proveedor'
    )
    
    quotation_filename = fields.Char(
        string='Nombre del Archivo'
    )
    
    # ===== Status Fields =====
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('sent', 'Enviada'),
        ('received', 'Recibida'),
        ('selected', 'Seleccionada'),
        ('rejected', 'Rechazada'),
    ], string='Estado', default='draft')
    
    is_selected = fields.Boolean(
        string='Seleccionada',
        help='Indica si esta cotización fue seleccionada'
    )
    
    notes = fields.Text(
        string='Notas',
        help='Notas adicionales sobre la cotización'
    )
    
    # ===== Related Fields =====
    project_id = fields.Many2one(
        'project.project',
        string='Proyecto',
        related='task_id.project_id',
        store=True,
        readonly=True
    )
    
    supplier_rating = fields.Float(
        string='Rating Proveedor',
        related='supplier_id.x_supplier_rating',
        readonly=True,
        store=False
    )
    
    # ===== Computed Fields =====
    @api.depends('price_unit', 'quantity')
    def _compute_price_total(self):
        """Calcular el precio total de la línea"""
        for line in self:
            line.price_total = line.price_unit * line.quantity
    
    # ===== Constraint Methods =====
    @api.constrains('quantity')
    def _check_quantity(self):
        """Validar que la cantidad sea positiva"""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(
                    self.env._('La cantidad debe ser mayor que cero.')
                )
    
    @api.constrains('price_unit')
    def _check_price_unit(self):
        """Validar que el precio sea positivo"""
        for line in self:
            if line.price_unit < 0:
                raise ValidationError(
                    self.env._('El precio unitario no puede ser negativo.')
                )
    
    @api.constrains('minimum_order_qty', 'quantity')
    def _check_moq(self):
        """Validar cantidad mínima de orden"""
        for line in self:
            if line.minimum_order_qty and line.quantity < line.minimum_order_qty:
                raise ValidationError(
                    self.env._('La cantidad cotizada no puede ser menor que el MOQ (%s).') % line.minimum_order_qty
                )
    
    # ===== Onchange Methods =====
    @api.onchange('supplier_id')
    def _onchange_supplier_id(self):
        """Actualizar información basada en el proveedor"""
        if self.supplier_id and self.task_id:
            # Buscar si el proveedor tiene los tags del producto
            matching_tags = self.supplier_id.x_product_tags & self.task_id.x_product_tags
            if matching_tags:
                # Podríamos pre-llenar información basada en experiencia previa
                pass
    
    @api.onchange('is_selected')
    def _onchange_is_selected(self):
        """Actualizar estado cuando se selecciona"""
        if self.is_selected:
            self.state = 'selected'
        elif self.state == 'selected':
            self.state = 'received'
    
    # ===== Business Methods =====
    def action_select_quotation(self):
        """Seleccionar esta cotización como ganadora"""
        self.ensure_one()
        
        # Desmarcar otras cotizaciones de la misma tarea
        other_lines = self.search([
            ('task_id', '=', self.task_id.id),
            ('id', '!=', self.id)
        ])
        other_lines.write({
            'is_selected': False,
            'state': 'rejected'
        })
        
        # Marcar esta como seleccionada
        self.write({
            'is_selected': True,
            'state': 'selected'
        })
        
        # Actualizar el proveedor seleccionado en la tarea
        self.task_id.x_selected_supplier_id = self.supplier_id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Cotización Seleccionada'),
                'message': self.env._('Se ha seleccionado la cotización de %s') % self.supplier_id.name,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_reject_quotation(self):
        """Rechazar esta cotización"""
        self.ensure_one()
        self.write({
            'is_selected': False,
            'state': 'rejected'
        })
    
    def action_mark_received(self):
        """Marcar cotización como recibida"""
        self.write({'state': 'received'})
    
    def action_view_supplier(self):
        """Ver ficha del proveedor"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.supplier_id.id,
            'view_mode': 'form',
        }
    
    @api.model
    def create_from_template(self, task_id, supplier_ids):
        """Crear líneas de cotización para múltiples proveedores"""
        task = self.env['project.task'].browse(task_id)
        if not task.exists():
            raise ValidationError(self.env._('La tarea no existe.'))
        
        lines = self.env['project.task.quotation.line']
        for supplier in self.env['res.partner'].browse(supplier_ids):
            if supplier.x_is_china_supplier:
                line_vals = {
                    'task_id': task_id,
                    'supplier_id': supplier.id,
                    'product_name': task.x_product_display_name,
                    'quantity': task.x_quantity_requested or 1.0,
                    'price_unit': 0.0,  # A completar
                    'state': 'sent',
                }
                lines |= self.create(line_vals)
        
        return lines
    
    # ===== Name Methods =====
    def name_get(self):
        """Nombre para mostrar"""
        result = []
        for line in self:
            name = f"{line.supplier_id.name} - {line.product_name} ({line.currency_id.symbol}{line.price_total:,.2f})"
            result.append((line.id, name))
        return result