# -*- coding: utf-8 -*-
{
    'name': 'Xportem Project Management',
    'version': '18.0.1.0.0',
    'category': 'Xportem/Project',
    'summary': 'Core procurement operations using projects and tasks',
    'description': """
Xportem Project Management
==========================

This module extends project management for procurement operations:
- Projects represent clients with consolidated metrics
- Tasks represent products to procure
- Quotation management system
- Supplier selection and evaluation

Key Features:
-------------
* Client-centric project structure
* Product procurement as tasks
* Multi-supplier quotation system
* Automatic supplier suggestions
* Request and evaluation workflows
* Integration with procurement tags and categories
    """,
    'author': 'Xportem',
    'website': 'https://www.xportem.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'project',
        'xportem_base',
        'xportem_contact',
        'purchase',  # Para integración futura con órdenes de compra
        'uom',       # Para unidades de medida
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data
        'data/project_stages_data.xml',
        
        # Views - Order matters!
        'views/project_task_views.xml',  # Define actions first
        'views/project_task_quotation_views.xml',
        'views/project_task_specs_views.xml',  # New technical specs views
        'views/project_project_views.xml',  # Then use them
        'views/xportem_project_menus.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 3,
}