# -*- coding: utf-8 -*-
{
    'name': 'Xportem Base',
    'version': '18.0.1.0.0',
    'summary': 'Base module for Xportem Procurement Suite',
    'description': """
        Base module for Xportem Procurement Suite
        ==========================================
        
        This module provides the foundation for the Xportem procurement system:
        * Master data models (categories, tags, certifications)
        * Base configurations and sequences
        * Common fields and methods for procurement processes
        
        Main Features:
        --------------
        * Procurement Categories with hierarchical structure
        * Procurement Tags for product classification
        * Certification management system
        * Sequence generators for procurement documents
    """,
    'author': 'Xportem',
    'website': 'https://github.com/OCA/xportem',
    'license': 'LGPL-3',
    'category': 'Procurement',
    'depends': [
        'base',
        'product',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data
        'data/procurement_sequence_data.xml',
        
        # Views
        'views/procurement_category_views.xml',
        'views/procurement_tag_views.xml',
        'views/procurement_certification_views.xml',
        'views/xportem_base_menus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}