# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ===== China Supplier Fields =====
    x_is_china_supplier = fields.Boolean(
        string='Es Proveedor China',
        help='Marcar si este contacto es un proveedor de China'
    )
    
    x_wechat_id = fields.Char(
        string='WeChat ID',
        help='Identificador de WeChat del contacto'
    )
    
    x_china_company_name = fields.Char(
        string='Nombre Empresa China',
        help='Nombre de la empresa en caracteres chinos'
    )
    
    x_china_province = fields.Selection(
        selection='_get_china_provinces',
        string='Provincia China',
        help='Provincia de China donde se ubica el proveedor'
    )
    
    x_china_city = fields.Char(
        string='Ciudad China',
        help='Ciudad específica en China'
    )
    
    x_product_categories = fields.Many2many(
        'procurement.category',
        'partner_procurement_category_rel',
        'partner_id',
        'category_id',
        string='Categorías de Productos',
        help='Categorías de productos que puede proveer'
    )
    
    x_product_tags = fields.Many2many(
        'procurement.tag',
        'partner_procurement_tag_rel',
        'partner_id',
        'tag_id',
        string='Productos que Vende',
        help='Etiquetas específicas de productos que vende'
    )
    
    x_certifications = fields.Many2many(
        'procurement.certification',
        'partner_procurement_certification_rel',
        'partner_id',
        'certification_id',
        string='Certificaciones',
        help='Certificaciones que posee el proveedor'
    )
    
    x_supplier_rating = fields.Float(
        string='Rating',
        digits=(3, 2),
        help='Calificación del proveedor (0-5)'
    )
    
    x_evaluation_date = fields.Date(
        string='Última Evaluación',
        help='Fecha de la última evaluación del proveedor'
    )
    
    x_factory_size = fields.Selection([
        ('small', 'Pequeña (<50 empleados)'),
        ('medium', 'Mediana (50-500 empleados)'),
        ('large', 'Grande (>500 empleados)')
    ], string='Tamaño de Fábrica')
    
    x_main_products = fields.Text(
        string='Productos Principales',
        help='Descripción de los principales productos que maneja'
    )
    
    # ===== Client Fields =====
    x_is_procurement_client = fields.Boolean(
        string='Cliente de Procura',
        help='Marcar si este contacto es un cliente del servicio de procura'
    )
    
    x_client_code = fields.Char(
        string='Código Cliente',
        help='Código único del cliente'
    )
    
    x_rif = fields.Char(
        string='RIF',
        help='Registro de Información Fiscal (Venezuela)'
    )
    
    # ===== User Role Fields =====
    x_client_role = fields.Selection([
        ('general_manager', 'Gerente General'),
        ('logistics', 'Equipo Logístico'),
        ('finance', 'Equipo Finanzas'),
        ('procurement', 'Equipo Compras'),
        ('requestor', 'Usuario Solicitante')
    ], string='Rol en Cliente',
       help='Rol del usuario dentro de la empresa cliente'
    )
    
    x_parent_client_id = fields.Many2one(
        'res.partner',
        string='Empresa Cliente',
        domain=[('x_is_procurement_client', '=', True)],
        help='Empresa cliente a la que pertenece este usuario'
    )
    
    # ===== Computed Fields =====
    x_is_china_configured = fields.Boolean(
        string='China Info Configurada',
        compute='_compute_china_configured',
        store=True,
        help='Indica si la información de China está completamente configurada'
    )
    
    x_tag_count = fields.Integer(
        string='Cantidad de Tags',
        compute='_compute_tag_count',
        store=False
    )
    
    x_certification_count = fields.Integer(
        string='Cantidad de Certificaciones',
        compute='_compute_certification_count',
        store=False
    )

    # ===== Compute Methods =====
    @api.depends('x_china_province', 'x_china_city', 'x_product_tags', 'x_product_categories')
    def _compute_china_configured(self):
        """Determina si la información de China está configurada"""
        for partner in self:
            partner.x_is_china_configured = bool(
                partner.x_china_province and 
                partner.x_china_city and 
                (partner.x_product_tags or partner.x_product_categories)
            )
    
    @api.depends('x_product_tags')
    def _compute_tag_count(self):
        """Cuenta la cantidad de tags asociadas"""
        for partner in self:
            partner.x_tag_count = len(partner.x_product_tags)
    
    @api.depends('x_certifications')
    def _compute_certification_count(self):
        """Cuenta la cantidad de certificaciones"""
        for partner in self:
            partner.x_certification_count = len(partner.x_certifications)

    # ===== Constraint Methods =====
    @api.constrains('x_supplier_rating')
    def _check_supplier_rating(self):
        """Valida que el rating esté entre 0 y 5"""
        for partner in self:
            if partner.x_supplier_rating:
                if partner.x_supplier_rating < 0 or partner.x_supplier_rating > 5:
                    raise ValidationError(
                        self.env._('El rating del proveedor debe estar entre 0 y 5.')
                    )
    
    @api.constrains('x_client_role', 'x_parent_client_id')
    def _check_client_role_consistency(self):
        """Valida consistencia entre rol y empresa cliente"""
        for partner in self:
            if partner.x_client_role and not partner.x_parent_client_id:
                raise ValidationError(
                    self.env._('Si se asigna un rol de cliente, debe especificar la empresa cliente.')
                )
    
    @api.constrains('x_is_china_supplier', 'x_is_procurement_client')
    def _check_partner_type_consistency(self):
        """Valida que un partner no sea proveedor y cliente al mismo tiempo"""
        for partner in self:
            if partner.x_is_china_supplier and partner.x_is_procurement_client:
                raise ValidationError(
                    self.env._('Un contacto no puede ser proveedor China y cliente de procura al mismo tiempo.')
                )

    # ===== Onchange Methods =====
    @api.onchange('x_is_china_supplier')
    def _onchange_is_china_supplier(self):
        """Limpia campos de cliente si se marca como proveedor"""
        if self.x_is_china_supplier:
            self.x_is_procurement_client = False
            self.x_client_role = False
            self.x_parent_client_id = False
            self.x_client_code = False
            self.x_rif = False
    
    @api.onchange('x_is_procurement_client')
    def _onchange_is_procurement_client(self):
        """Limpia campos de proveedor si se marca como cliente"""
        if self.x_is_procurement_client:
            self.x_is_china_supplier = False
            self.x_wechat_id = False
            self.x_china_company_name = False
            self.x_china_province = False
            self.x_china_city = False
            self.x_product_categories = False
            self.x_product_tags = False
            self.x_certifications = False
            self.x_supplier_rating = False
            self.x_evaluation_date = False
            self.x_factory_size = False
            self.x_main_products = False
    
    @api.onchange('x_china_province')
    def _onchange_china_province(self):
        """Limpia la ciudad cuando cambia la provincia"""
        if self.x_china_province:
            self.x_china_city = False

    # ===== Business Methods =====
    @api.model
    def search_suppliers_by_product(self, product_keywords):
        """
        Buscar proveedores por palabras clave de producto
        
        Args:
            product_keywords: String con palabras clave a buscar
            
        Returns:
            Recordset de proveedores que coinciden
        """
        if not product_keywords:
            return self.env['res.partner']
        
        domain = [
            ('x_is_china_supplier', '=', True),
            '|', '|', '|',
            ('x_product_tags.name', 'ilike', product_keywords),
            ('x_product_tags.alternative_names', 'ilike', product_keywords),
            ('x_main_products', 'ilike', product_keywords),
            ('x_product_categories.name', 'ilike', product_keywords)
        ]
        
        return self.search(domain, order='x_supplier_rating desc')
    
    @api.model
    def search_suppliers_by_category(self, category_id):
        """
        Buscar proveedores por categoría específica
        
        Args:
            category_id: ID de la categoría a buscar
            
        Returns:
            Recordset de proveedores en esa categoría
        """
        domain = [
            ('x_is_china_supplier', '=', True),
            ('x_product_categories', 'in', [category_id])
        ]
        
        return self.search(domain, order='x_supplier_rating desc')
    
    @api.model
    def search_suppliers_by_certification(self, certification_ids):
        """
        Buscar proveedores por certificaciones requeridas
        
        Args:
            certification_ids: Lista de IDs de certificaciones
            
        Returns:
            Recordset de proveedores con esas certificaciones
        """
        domain = [
            ('x_is_china_supplier', '=', True),
            ('x_certifications', 'in', certification_ids)
        ]
        
        return self.search(domain, order='x_supplier_rating desc')
    
    def rate_supplier(self, rating, evaluation_notes=None):
        """
        Actualiza el rating del proveedor
        
        Args:
            rating: Nueva calificación (0-5)
            evaluation_notes: Notas opcionales de la evaluación
        """
        self.ensure_one()
        if not self.x_is_china_supplier:
            raise ValidationError(
                self.env._('Solo se pueden calificar proveedores de China.')
            )
        
        vals = {
            'x_supplier_rating': rating,
            'x_evaluation_date': fields.Date.today()
        }
        
        if evaluation_notes:
            # Preparado para campo de notas en futuras versiones
            pass
        
        self.write(vals)
        
        return True

    # ===== Selection Methods =====
    @api.model
    def _get_china_provinces(self):
        """Retorna la lista de provincias de China"""
        return [
            ('anhui', 'Anhui'),
            ('beijing', 'Beijing'),
            ('chongqing', 'Chongqing'),
            ('fujian', 'Fujian'),
            ('gansu', 'Gansu'),
            ('guangdong', 'Guangdong'),
            ('guangxi', 'Guangxi'),
            ('guizhou', 'Guizhou'),
            ('hainan', 'Hainan'),
            ('hebei', 'Hebei'),
            ('heilongjiang', 'Heilongjiang'),
            ('henan', 'Henan'),
            ('hubei', 'Hubei'),
            ('hunan', 'Hunan'),
            ('jiangsu', 'Jiangsu'),
            ('jiangxi', 'Jiangxi'),
            ('jilin', 'Jilin'),
            ('liaoning', 'Liaoning'),
            ('inner_mongolia', 'Mongolia Interior'),
            ('ningxia', 'Ningxia'),
            ('qinghai', 'Qinghai'),
            ('shaanxi', 'Shaanxi'),
            ('shandong', 'Shandong'),
            ('shanghai', 'Shanghai'),
            ('shanxi', 'Shanxi'),
            ('sichuan', 'Sichuan'),
            ('tianjin', 'Tianjin'),
            ('tibet', 'Tibet'),
            ('xinjiang', 'Xinjiang'),
            ('yunnan', 'Yunnan'),
            ('zhejiang', 'Zhejiang'),
            ('hong_kong', 'Hong Kong'),
            ('macau', 'Macau'),
            ('taiwan', 'Taiwan'),
        ]

    # ===== Override Methods =====
    @api.model_create_multi
    def create(self, vals_list):
        """Override para generar código de cliente automático"""
        for vals in vals_list:
            if vals.get('x_is_procurement_client') and not vals.get('x_client_code'):
                vals['x_client_code'] = self.env['ir.sequence'].next_by_code('procurement.client') or 'New'
        
        return super().create(vals_list)
    
    def write(self, vals):
        """Override para validaciones adicionales en escritura"""
        # Si se marca como cliente y no tiene código, generarlo
        if vals.get('x_is_procurement_client') and not self.x_client_code:
            vals['x_client_code'] = self.env['ir.sequence'].next_by_code('procurement.client') or 'New'
        
        return super().write(vals)