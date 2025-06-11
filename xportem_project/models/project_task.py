# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    # ===== Product Identification Fields =====
    x_product_id = fields.Many2one(
        'product.product',
        string='Producto Existente',
        help='Seleccionar un producto del catálogo existente'
    )
    
    x_product_name_free = fields.Char(
        string='Producto Solicitado',
        help='Nombre del producto cuando no existe en el catálogo'
    )
    
    x_product_tags = fields.Many2many(
        'procurement.tag',
        'task_procurement_tag_rel',
        'task_id',
        'tag_id',
        string='Tags del Producto',
        help='Etiquetas para identificar el tipo de producto'
    )
    
    x_category_id = fields.Many2one(
        'procurement.category',
        string='Categoría',
        help='Categoría principal del producto'
    )
    
    # ===== Request Information Fields =====
    x_request_description = fields.Text(
        string='Descripción de la Solicitud',
        help='Descripción detallada de la solicitud del cliente'
    )
    
    x_request_file = fields.Binary(
        string='Ficha de Solicitud',
        help='Archivo con especificaciones técnicas'
    )
    
    x_request_filename = fields.Char(
        string='Nombre del Archivo'
    )
    
    x_quantity_requested = fields.Float(
        string='Cantidad Solicitada',
        digits='Product Unit of Measure',
        help='Cantidad requerida por el cliente'
    )
    
    x_uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de Medida',
        help='Unidad de medida del producto'
    )
    
    x_required_date = fields.Date(
        string='Fecha Requerida',
        help='Fecha en que el cliente necesita el producto'
    )
    
    x_urgency = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgente'),
        ('critical', 'Crítico')
    ], string='Urgencia', default='normal')
    
    x_budget_estimated = fields.Monetary(
        string='Presupuesto Estimado',
        currency_field='currency_id',
        help='Presupuesto estimado para esta compra'
    )
    
    # ===== Supplier Fields =====
    x_suggested_supplier_ids = fields.Many2many(
        'res.partner',
        'task_suggested_supplier_rel',
        'task_id',
        'partner_id',
        string='Proveedores Sugeridos',
        compute='_compute_suggested_suppliers',
        store=False,
        domain=[('x_is_china_supplier', '=', True)],
        help='Proveedores sugeridos basados en los tags del producto'
    )
    
    x_potential_supplier_ids = fields.Many2many(
        'res.partner',
        'task_potential_supplier_rel',
        'task_id',
        'partner_id',
        string='Proveedores Potenciales',
        domain=[('x_is_china_supplier', '=', True)],
        help='Proveedores considerados para esta compra'
    )
    
    x_selected_supplier_id = fields.Many2one(
        'res.partner',
        string='Proveedor Seleccionado',
        domain=[('x_is_china_supplier', '=', True)],
        help='Proveedor finalmente seleccionado'
    )
    
    # ===== Status Fields =====
    x_is_request = fields.Boolean(
        string='Es Solicitud',
        help='Marcar cuando es una solicitud formal del cliente'
    )
    
    x_is_evaluation = fields.Boolean(
        string='En Evaluación',
        help='Marcar cuando está en proceso de evaluación'
    )
    
    x_is_purchased = fields.Boolean(
        string='Compra Realizada',
        help='Indica si ya se realizó la orden de compra'
    )
    
    x_purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Orden de Compra',
        help='Orden de compra relacionada'
    )
    
    x_approval_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ], string='Estado de Aprobación', default='pending')
    
    # ===== Quotation Fields =====
    x_quotation_line_ids = fields.One2many(
        'project.task.quotation.line',
        'task_id',
        string='Líneas de Cotización'
    )
    
    x_quotation_count = fields.Integer(
        string='Número de Cotizaciones',
        compute='_compute_quotation_count',
        store=False
    )
    
    # ===== Technical Specifications Fields =====
    x_technical_specs_ids = fields.One2many(
        'project.task.technical.specs',
        'task_id',
        string='Especificaciones Técnicas'
    )
    
    x_has_technical_specs = fields.Boolean(
        string='Tiene Especificaciones',
        compute='_compute_has_technical_specs',
        store=True
    )
    
    # ===== Computed Display Fields =====
    x_product_display_name = fields.Char(
        string='Producto',
        compute='_compute_product_display_name',
        store=True,
        help='Nombre del producto para mostrar'
    )
    
    x_supplier_match_score = fields.Float(
        string='Score de Coincidencia',
        compute='_compute_suggested_suppliers',
        store=False,
        help='Porcentaje de coincidencia con proveedores'
    )
    
    # ===== Currency field for monetary =====
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id
    )
    
    # ===== Compute Methods =====
    @api.depends('x_technical_specs_ids')
    def _compute_has_technical_specs(self):
        """Determinar si la tarea tiene especificaciones técnicas"""
        for task in self:
            task.x_has_technical_specs = bool(task.x_technical_specs_ids)
    
    @api.depends('x_product_id', 'x_product_name_free')
    def _compute_product_display_name(self):
        """Calcular el nombre del producto a mostrar"""
        for task in self:
            if task.x_product_id:
                task.x_product_display_name = task.x_product_id.display_name
            else:
                task.x_product_display_name = task.x_product_name_free or ''
    
    @api.depends('x_product_tags', 'x_category_id')
    def _compute_suggested_suppliers(self):
        """Calcular proveedores sugeridos basados en tags y categoría"""
        Partner = self.env['res.partner']
        
        for task in self:
            if not task.x_product_tags and not task.x_category_id:
                task.x_suggested_supplier_ids = Partner
                task.x_supplier_match_score = 0.0
                continue
            
            # Buscar proveedores por tags
            suppliers_by_tags = Partner
            if task.x_product_tags:
                suppliers_by_tags = Partner.search([
                    ('x_is_china_supplier', '=', True),
                    ('x_product_tags', 'in', task.x_product_tags.ids)
                ])
            
            # Buscar proveedores por categoría
            suppliers_by_category = Partner
            if task.x_category_id:
                suppliers_by_category = Partner.search([
                    ('x_is_china_supplier', '=', True),
                    ('x_product_categories', 'in', [task.x_category_id.id])
                ])
            
            # Combinar y ordenar por rating
            all_suppliers = (suppliers_by_tags | suppliers_by_category)
            task.x_suggested_supplier_ids = all_suppliers.sorted(
                key=lambda p: p.x_supplier_rating, 
                reverse=True
            )[:10]  # Top 10 proveedores
            
            # Calcular score de coincidencia
            if task.x_suggested_supplier_ids:
                task.x_supplier_match_score = 100.0
            else:
                task.x_supplier_match_score = 0.0
    
    @api.depends('x_quotation_line_ids')
    def _compute_quotation_count(self):
        """Contar número de cotizaciones"""
        for task in self:
            suppliers = task.x_quotation_line_ids.mapped('supplier_id')
            task.x_quotation_count = len(suppliers.ids)
    
    # ===== Onchange Methods =====
    @api.onchange('x_product_id')
    def _onchange_product_id(self):
        """Actualizar información cuando se selecciona un producto"""
        if self.x_product_id:
            # Limpiar nombre libre si se selecciona producto
            self.x_product_name_free = False
            
            # Heredar UOM del producto
            self.x_uom_id = self.x_product_id.uom_id
            
            # Sugerir categoría basada en el producto (si existe relación)
            # Por ahora no hay relación directa, se puede agregar después
    
    @api.onchange('x_product_tags')
    def _onchange_product_tags(self):
        """Actualizar proveedores sugeridos al cambiar tags"""
        # El compute method se encargará de esto automáticamente
        pass
    
    @api.onchange('x_is_request')
    def _onchange_is_request(self):
        """Cambiar el nombre de la tarea cuando se marca como solicitud"""
        if self.x_is_request and not self.name:
            if self.x_product_display_name:
                self.name = f"Solicitud: {self.x_product_display_name}"
    
    # ===== Constraint Methods =====
    @api.constrains('x_product_id', 'x_product_name_free')
    def _check_product_definition(self):
        """Validar que se defina el producto de alguna forma"""
        for task in self:
            if task.x_is_request and not task.x_product_id and not task.x_product_name_free:
                raise ValidationError(
                    self.env._('Debe especificar un producto existente o ingresar el nombre del producto solicitado.')
                )
    
    @api.constrains('x_selected_supplier_id', 'x_potential_supplier_ids')
    def _check_supplier_consistency(self):
        """Validar que el proveedor seleccionado esté en los potenciales"""
        for task in self:
            if task.x_selected_supplier_id and task.x_potential_supplier_ids:
                if task.x_selected_supplier_id not in task.x_potential_supplier_ids:
                    raise ValidationError(
                        self.env._('El proveedor seleccionado debe estar en la lista de proveedores potenciales.')
                    )
    
    # ===== Override Methods =====
    @api.model_create_multi
    def create(self, vals_list):
        """Override para lógica adicional en creación"""
        tasks = super().create(vals_list)
        
        for task in tasks:
            # Auto-generar nombre si no existe
            if not task.name and task.x_product_display_name:
                task.name = f"Procura: {task.x_product_display_name}"
            
            # Si es solicitud y no hay proveedores potenciales, copiar los sugeridos
            if task.x_is_request and task.x_suggested_supplier_ids and not task.x_potential_supplier_ids:
                task.x_potential_supplier_ids = task.x_suggested_supplier_ids[:5]  # Top 5
        
        return tasks
    
    # ===== Business Methods =====
    def action_view_quotations(self):
        """Ver todas las cotizaciones de esta tarea"""
        self.ensure_one()
        
        action = {
            'name': f'Cotizaciones - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.quotation.line',
            'view_mode': 'list,form',
            'domain': [('task_id', '=', self.id)],
            'context': {
                'default_task_id': self.id,
                'group_by': 'supplier_id',
            },
        }
        
        return action
    
    def action_create_quotation(self):
        """Crear nueva línea de cotización"""
        self.ensure_one()
        
        return {
            'name': 'Nueva Cotización',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.quotation.line',
            'view_mode': 'form',
            'context': {
                'default_task_id': self.id,
                'default_product_name': self.x_product_display_name,
                'default_quantity': self.x_quantity_requested,
            },
            'target': 'new',
        }
    
    def action_create_purchase_order(self):
        """Crear orden de compra desde la tarea"""
        self.ensure_one()
        
        if not self.x_selected_supplier_id:
            raise ValidationError(
                self.env._('Debe seleccionar un proveedor antes de crear la orden de compra.')
            )
        
        # Preparar valores para la orden de compra
        po_vals = {
            'partner_id': self.x_selected_supplier_id.id,
            'origin': self.name,
            'notes': f"Solicitud: {self.x_request_description or ''}",
        }
        
        # Crear la orden de compra
        purchase_order = self.env['purchase.order'].create(po_vals)
        
        # Marcar la tarea
        self.write({
            'x_is_purchased': True,
            'x_purchase_order_id': purchase_order.id,
        })
        
        # Abrir la orden de compra
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_mode': 'form',
        }
    
    def action_create_technical_specs(self):
        """Crear o editar especificaciones técnicas"""
        self.ensure_one()
        
        # Buscar si ya existe una especificación
        specs = self.x_technical_specs_ids[:1]  # Tomar la primera si existe
        
        if specs:
            # Si existe, abrir en modo edición
            return {
                'name': 'Especificaciones Técnicas',
                'type': 'ir.actions.act_window',
                'res_model': 'project.task.technical.specs',
                'res_id': specs.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            # Si no existe, crear nueva
            return {
                'name': 'Nueva Especificación Técnica',
                'type': 'ir.actions.act_window',
                'res_model': 'project.task.technical.specs',
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'default_task_id': self.id,
                    'default_product_name': self.x_product_display_name,
                    'default_quantity_required': self.x_quantity_requested,
                }
            }
    
    def action_approve_request(self):
        """Aprobar la solicitud"""
        self.ensure_one()
        self.x_approval_status = 'approved'
    
    def action_reject_request(self):
        """Rechazar la solicitud"""
        self.ensure_one()
        self.x_approval_status = 'rejected'