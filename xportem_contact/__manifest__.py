# -*- coding: utf-8 -*-
{
    'name': 'Xportem Contact Management',
    'version': '18.0.1.0.0',
    'category': 'Xportem/Contact',
    'summary': 'Extended contact management for China suppliers and client roles',
    'description': """
Xportem Contact Management
==========================

This module extends contact management with:
- China supplier specific fields (WeChat ID, province, city)
- Product tags and certifications for suppliers
- Client role management
- Smart supplier search capabilities

Key Features:
-------------
* China Supplier Fields
* Client Role System
* Product Tag Integration
* Certification Management
* Supplier Rating System
* Smart Search Methods
    """,
    'author': 'Xportem',
    'website': 'https://www.xportem.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'xportem_base',  # Para usar procurement.tag, procurement.category, procurement.certification
        'contacts',      # Para extender vistas de contactos
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Views
        'views/res_partner_views.xml',
        'views/xportem_contact_menus.xml',
        
        # Data
        'data/china_provinces_data.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 2,
}