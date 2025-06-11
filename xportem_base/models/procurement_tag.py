# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProcurementTag(models.Model):
    _name = 'procurement.tag'  # IMPORTANT: Not 'product.tag' to avoid conflicts
    _description = 'Procurement Product Tag'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'sequence, complete_name'
    
    # Basic Fields
    name = fields.Char(
        'Tag Name', 
        required=True, 
        index=True,
        translate=True,
        help="Main name for the tag (e.g., SS304, Gate Valve)"
    )
    code = fields.Char(
        'Tag Code', 
        size=20,
        index=True,
        help="Unique code for the tag"
    )
    sequence = fields.Integer(
        'Sequence', 
        default=10,
        help="Sequence for ordering tags"
    )
    active = fields.Boolean(
        'Active', 
        default=True,
        help="If unchecked, it will allow you to hide the tag without removing it."
    )
    color = fields.Integer(
        'Color Index',
        default=0,
        help="Color index for tag display"
    )
    
    # Hierarchical Fields
    parent_id = fields.Many2one(
        'procurement.tag', 
        'Parent Tag', 
        index=True, 
        ondelete='cascade'
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        'procurement.tag', 
        'parent_id', 
        'Child Tags'
    )
    
    # Relationship Fields
    category_id = fields.Many2one(
        'procurement.category',
        'Related Category',
        help="Main category this tag belongs to"
    )
    
    # Computed Fields
    complete_name = fields.Char(
        'Complete Name',
        compute='_compute_complete_name',
        store=True
    )
    child_count = fields.Integer(
        'Child Count',
        compute='_compute_child_count',
        store=False  # Important: store=False to avoid search issues
    )
    supplier_count = fields.Integer(
        'Supplier Count',
        compute='_compute_usage_stats',
        store=False  # Important: store=False to avoid search issues
    )
    project_count = fields.Integer(
        'Project Count',
        compute='_compute_usage_stats',
        store=False  # Important: store=False to avoid search issues
    )
    
    # Search Enhancement Fields
    alternative_names = fields.Text(
        'Alternative Names',
        translate=True,
        help="Alternative names or synonyms for this tag, separated by commas. "
             "E.g., 'stainless steel, inox, acero inoxidable'"
    )
    keywords = fields.Text(
        'Search Keywords',
        translate=True,
        help="Additional keywords to help find this tag in searches"
    )
    description = fields.Text(
        'Description',
        translate=True,
        help="Detailed description of products covered by this tag"
    )
    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for tag in self:
            if tag.parent_id:
                tag.complete_name = f"{tag.parent_id.complete_name} / {tag.name}"
            else:
                tag.complete_name = tag.name
    
    @api.depends('child_ids')
    def _compute_child_count(self):
        for tag in self:
            tag.child_count = len(tag.child_ids)
    
    def _compute_usage_stats(self):
        """Compute usage statistics for tags"""
        for tag in self:
            # These will be properly computed when xportem_contact and xportem_project are installed
            tag.supplier_count = 0
            tag.project_count = 0
    
    @api.constrains('parent_id')
    def _check_tag_recursion(self):
        if not self._check_recursion():
            raise ValidationError(
                self.env._('You cannot create recursive tags.')
            )
    
    @api.model
    def name_create(self, name):
        """Allow quick creation of tags from many2one fields"""
        return self.create({'name': name}).name_get()[0]
    
    def name_get(self):
        """Return complete hierarchical name for display"""
        result = []
        for tag in self:
            if self._context.get('complete_name'):
                result.append((tag.id, tag.complete_name))
            else:
                result.append((tag.id, tag.name))
        return result
    
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=100, order=None):
        """Enhanced search including code, alternative names and keywords"""
        domain = domain or []
        if name:
            # First try exact matches
            exact_domain = ['|', '|', '|',
                           ('name', '=', name),
                           ('code', '=', name),
                           ('alternative_names', '=', name),
                           ('keywords', '=', name)
                           ] + domain
            result = self._search(exact_domain, limit=limit, order=order)
            
            # If no exact matches, try partial matches
            if not result:
                domain = ['|', '|', '|', '|',
                         ('name', operator, name),
                         ('code', operator, name),
                         ('complete_name', operator, name),
                         ('alternative_names', operator, name),
                         ('keywords', operator, name)
                         ] + domain
                result = self._search(domain, limit=limit, order=order)
            
            return result
        return self._search(domain, limit=limit, order=order)