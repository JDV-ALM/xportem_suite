# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectTaskTechnicalSpecs(models.Model):
    _name = 'project.task.technical.specs'
    _description = 'Especificaciones Técnicas del Producto'
    _rec_name = 'product_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # ===== Relación con Tarea =====
    task_id = fields.Many2one(
        'project.task',
        string='Tarea',
        required=True,
        ondelete='cascade',
        help='Tarea de procura relacionada'
    )
    
    # ===== Descripción General =====
    product_name = fields.Char(
        string='Nombre del Producto',
        required=True,
        tracking=True,
        help='Nombre comercial/técnico del producto'
    )
    
    detailed_description = fields.Text(
        string='Descripción Detallada',
        tracking=True,
        help='Función, características principales'
    )
    
    quantity_required = fields.Float(
        string='Cantidad Requerida',
        tracking=True,
        help='Cantidad que se requiere del producto'
    )
    
    product_category = fields.Selection([
        ('equipment', 'Equipo'),
        ('component', 'Componente'),
        ('material', 'Material'),
        ('instrument', 'Instrumento'),
        ('other', 'Otro')
    ], string='Categoría del Producto', default='equipment', tracking=True)
    
    # ===== Caso de Uso y Aplicación =====
    specific_application = fields.Text(
        string='Aplicación Específica',
        help='Dónde y cómo se utilizará el producto'
    )
    
    process_system = fields.Char(
        string='Proceso/Sistema',
        help='Sistema o proceso donde se utilizará'
    )
    
    main_function = fields.Text(
        string='Función Principal',
        help='Qué debe hacer el producto en la aplicación'
    )
    
    criticality = fields.Selection([
        ('critical', 'Crítico para operación'),
        ('important', 'Importante'),
        ('spare', 'Repuesto')
    ], string='Criticidad', default='important', tracking=True)
    
    # ===== Características Dimensionales =====
    length = fields.Float(
        string='Largo',
        help='Largo en milímetros'
    )
    
    width = fields.Float(
        string='Ancho',
        help='Ancho en milímetros'
    )
    
    height = fields.Float(
        string='Alto',
        help='Alto en milímetros'
    )
    
    dimension_unit = fields.Selection([
        ('mm', 'mm'),
        ('cm', 'cm'),
        ('m', 'm'),
        ('in', 'pulgadas'),
        ('ft', 'pies')
    ], string='Unidad de Dimensión', default='mm')
    
    approximate_weight = fields.Float(
        string='Peso Aproximado',
        help='Peso en kilogramos'
    )
    
    weight_unit = fields.Selection([
        ('kg', 'kg'),
        ('g', 'g'),
        ('lb', 'lb'),
        ('ton', 'ton')
    ], string='Unidad de Peso', default='kg')
    
    dimensional_tolerance = fields.Char(
        string='Tolerancias Dimensionales',
        help='±mm o % según aplicabilidad'
    )
    
    connections_interfaces = fields.Text(
        string='Conexiones/Interfaces',
        help='Tipo y tamaño de conexiones'
    )
    
    # ===== Especificaciones de Material =====
    main_material = fields.Char(
        string='Material Principal',
        help='Acero, aluminio, plástico, etc.'
    )
    
    grade_alloy = fields.Char(
        string='Grado/Aleación',
        help='AISI 316L, 6061-T6, etc.'
    )
    
    surface_finish = fields.Char(
        string='Acabado Superficial',
        help='Galvanizado, anodizado, pintado, etc.'
    )
    
    chemical_resistance = fields.Text(
        string='Resistencia Química',
        help='Compatibilidad con fluidos/ambiente'
    )
    
    # ===== Condiciones de Operación =====
    working_pressure = fields.Float(
        string='Presión de Trabajo',
        help='Presión en bar'
    )
    
    pressure_unit = fields.Selection([
        ('bar', 'bar'),
        ('psi', 'psi'),
        ('kpa', 'kPa'),
        ('mpa', 'MPa')
    ], string='Unidad de Presión', default='bar')
    
    min_temperature = fields.Float(
        string='Temperatura Mínima',
        help='Temperatura mínima en °C'
    )
    
    max_temperature = fields.Float(
        string='Temperatura Máxima',
        help='Temperatura máxima en °C'
    )
    
    installation_environment = fields.Selection([
        ('indoor', 'Interior'),
        ('outdoor', 'Exterior'),
        ('corrosive', 'Corrosivo'),
        ('explosive', 'Explosivo'),
        ('clean_room', 'Sala Limpia'),
        ('marine', 'Marino')
    ], string='Ambiente de Instalación', default='indoor')
    
    # Especificaciones Eléctricas
    voltage = fields.Float(
        string='Voltaje',
        help='Voltaje en V'
    )
    
    frequency = fields.Float(
        string='Frecuencia',
        help='Frecuencia en Hz'
    )
    
    phases = fields.Selection([
        ('single', 'Monofásico'),
        ('three', 'Trifásico')
    ], string='Fases')
    
    power_consumption = fields.Float(
        string='Consumo de Potencia',
        help='Consumo en kW'
    )
    
    # Especificaciones de Rendimiento
    flow_capacity = fields.Float(
        string='Caudal/Capacidad',
        help='Caudal o capacidad según el tipo de producto'
    )
    
    flow_unit = fields.Char(
        string='Unidad de Caudal',
        help='m³/h, L/min, etc.'
    )
    
    performance_specs = fields.Text(
        string='Especificaciones de Rendimiento',
        help='Otras especificaciones de rendimiento relevantes'
    )
    
    # ===== Campos Adicionales =====
    notes = fields.Text(
        string='Notas Adicionales',
        help='Cualquier información adicional relevante'
    )
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'task_specs_attachment_rel',
        'specs_id',
        'attachment_id',
        string='Archivos Adjuntos',
        help='Diagramas, planos, fichas técnicas, etc.'
    )
    
    # ===== Campos Computados =====
    dimensions_display = fields.Char(
        string='Dimensiones',
        compute='_compute_dimensions_display',
        store=True
    )
    
    @api.depends('length', 'width', 'height', 'dimension_unit')
    def _compute_dimensions_display(self):
        """Mostrar las dimensiones en formato legible"""
        for spec in self:
            if spec.length or spec.width or spec.height:
                dims = []
                if spec.length:
                    dims.append(f"{spec.length}")
                if spec.width:
                    dims.append(f"{spec.width}")
                if spec.height:
                    dims.append(f"{spec.height}")
                
                if dims:
                    spec.dimensions_display = f"{' x '.join(dims)} {spec.dimension_unit or 'mm'}"
                else:
                    spec.dimensions_display = False
            else:
                spec.dimensions_display = False
    
    # ===== Override Methods =====
    @api.model_create_multi
    def create(self, vals_list):
        """Override para lógica adicional en creación"""
        specs = super().create(vals_list)
        
        for spec in specs:
            # Si la tarea no tiene nombre de producto libre, actualizarlo
            if spec.task_id and not spec.task_id.x_product_name_free:
                spec.task_id.x_product_name_free = spec.product_name
        
        return specs
    
    def write(self, vals):
        """Override para sincronizar con la tarea"""
        res = super().write(vals)
        
        # Si se actualiza el nombre del producto, actualizar la tarea
        if 'product_name' in vals:
            for spec in self:
                if spec.task_id and not spec.task_id.x_product_id:
                    spec.task_id.x_product_name_free = vals['product_name']
        
        return res
    
    # ===== Business Methods =====
    def action_generate_pdf(self):
        """Generar PDF con las especificaciones técnicas"""
        self.ensure_one()
        # TODO: Implementar generación de PDF
        return {
            'type': 'ir.actions.report',
            'report_name': 'xportem_project.technical_specs_report',
            'report_type': 'qweb-pdf',
            'res_model': 'project.task.technical.specs',
            'res_id': self.id,
        }
    
    def action_duplicate_specs(self):
        """Duplicar especificaciones para otra tarea"""
        self.ensure_one()
        return {
            'name': 'Duplicar Especificaciones',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task.technical.specs.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_source_specs_id': self.id,
            }
        }