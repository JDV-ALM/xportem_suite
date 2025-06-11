# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProcurementCategory(models.Model):
    _name = 'procurement.category'
    _description = 'Procurement Product Category'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'sequence, complete_name'
    
    # Basic Fields
    name = fields.Char(
        'Category Name', 
        required=True, 
        index=True,
        translate=True
    )
    code = fields.Char(
        'Category Code', 
        size=10,
        help="Short code for the category (e.g., IND, STL, VLV)"
    )
    sequence = fields.Integer(
        'Sequence', 
        default=10,
        help="Sequence for ordering categories"
    )
    active = fields.Boolean(
        'Active', 
        default=True,
        help="If unchecked, it will allow you to hide the category without removing it."
    )
    
    # Hierarchical Fields
    parent_id = fields.Many2one(
        'procurement.category', 
        'Parent Category', 
        index=True, 
        ondelete='cascade'
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        'procurement.category', 
        'parent_id', 
        'Child Categories'
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
    
    # Additional Fields
    description = fields.Text(
        'Description',
        translate=True,
        help="Detailed description of what products belong to this category"
    )
    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = f"{category.parent_id.complete_name} / {category.name}"
            else:
                category.complete_name = category.name
    
    @api.depends('child_ids')
    def _compute_child_count(self):
        for category in self:
            category.child_count = len(category.child_ids)
    
    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(
                self.env._('You cannot create recursive categories.')
            )
    
    @api.model
    def name_create(self, name):
        """Allow quick creation of categories from many2one fields"""
        return self.create({'name': name}).name_get()[0]
    
    def name_get(self):
        """Return complete hierarchical name for display"""
        result = []
        for category in self:
            if self._context.get('complete_name'):
                result.append((category.id, category.complete_name))
            else:
                result.append((category.id, category.name))
        return result
    
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=100, order=None):
        """Enhanced search including code and complete name"""
        domain = domain or []
        if name:
            domain = ['|', '|',
                     ('name', operator, name),
                     ('code', operator, name),
                     ('complete_name', operator, name)
                     ] + domain
        return self._search(domain, limit=limit, order=order)