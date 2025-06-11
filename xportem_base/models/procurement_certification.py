# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProcurementCertification(models.Model):
    _name = 'procurement.certification'
    _description = 'Procurement Certification'
    _order = 'sequence, name'
    
    # Basic Fields
    name = fields.Char(
        'Certification Name', 
        required=True, 
        index=True,
        translate=True,
        help="Name of the certification (e.g., ISO 9001, CE Mark, API 6D)"
    )
    code = fields.Char(
        'Certification Code', 
        size=20,
        index=True,
        help="Short code for the certification"
    )
    sequence = fields.Integer(
        'Sequence', 
        default=10,
        help="Sequence for ordering certifications"
    )
    active = fields.Boolean(
        'Active', 
        default=True,
        help="If unchecked, it will allow you to hide the certification without removing it."
    )
    
    # Classification Fields
    certification_type = fields.Selection([
        ('quality', 'Quality Management'),
        ('safety', 'Safety Standards'),
        ('environmental', 'Environmental'),
        ('industry', 'Industry Specific'),
        ('product', 'Product Certification'),
        ('process', 'Process Certification'),
        ('other', 'Other')
    ], string='Certification Type', required=True, default='quality')
    
    priority = fields.Selection([
        ('mandatory', 'Mandatory'),
        ('recommended', 'Recommended'),
        ('optional', 'Optional')
    ], string='Priority Level', default='recommended',
       help="Indicates how critical this certification is for procurement")
    
    # Detailed Information
    authority = fields.Char(
        'Issuing Authority',
        help="Organization that issues this certification (e.g., ISO, API, ASME)"
    )
    description = fields.Text(
        'Description',
        translate=True,
        help="Detailed description of what this certification covers"
    )
    requirements = fields.Text(
        'Requirements',
        translate=True,
        help="Key requirements to obtain this certification"
    )
    
    # Validity Information
    validity_period = fields.Integer(
        'Validity Period (months)',
        help="Standard validity period in months (0 = perpetual)"
    )
    requires_renewal = fields.Boolean(
        'Requires Renewal',
        compute='_compute_requires_renewal',
        store=True
    )
    
    # Scope Fields
    country_ids = fields.Many2many(
        'res.country',
        'procurement_certification_country_rel',
        'certification_id',
        'country_id',
        string='Applicable Countries',
        help="Countries where this certification is required or recognized"
    )
    industry_ids = fields.Many2many(
        'procurement.category',
        'procurement_certification_category_rel',
        'certification_id',
        'category_id',
        string='Applicable Industries',
        help="Product categories where this certification is typically required"
    )
    
    # Documentation Fields
    website = fields.Char(
        'Official Website',
        help="Official website for certification information"
    )
    documentation_url = fields.Char(
        'Documentation URL',
        help="Link to certification documentation or standards"
    )
    
    # Usage Statistics
    supplier_count = fields.Integer(
        'Supplier Count',
        compute='_compute_usage_stats',
        store=False  # Important: store=False to avoid search issues
    )
    
    # Business Logic Fields
    is_mandatory = fields.Boolean(
        'Is Mandatory',
        help="Indicates if this certification is mandatory for certain products/regions"
    )
    notes = fields.Text(
        'Internal Notes',
        help="Internal notes about this certification"
    )
    
    @api.depends('validity_period')
    def _compute_requires_renewal(self):
        for cert in self:
            cert.requires_renewal = bool(cert.validity_period and cert.validity_period > 0)
    
    def _compute_usage_stats(self):
        """Compute usage statistics for certifications"""
        for cert in self:
            # This will be properly computed when xportem_contact is installed
            cert.supplier_count = 0
    
    @api.model
    def name_create(self, name):
        """Allow quick creation of certifications from many2one fields"""
        return self.create({'name': name}).name_get()[0]
    
    def name_get(self):
        """Return name with code if available"""
        result = []
        for cert in self:
            if cert.code:
                name = f"[{cert.code}] {cert.name}"
            else:
                name = cert.name
            result.append((cert.id, name))
        return result
    
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=100, order=None):
        """Enhanced search including code and authority"""
        domain = domain or []
        if name:
            domain = ['|', '|',
                     ('name', operator, name),
                     ('code', operator, name),
                     ('authority', operator, name)
                     ] + domain
        return self._search(domain, limit=limit, order=order)