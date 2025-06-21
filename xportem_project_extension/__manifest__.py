# -*- coding: utf-8 -*-
{
    'name': 'Xportem Project Extension',
    'version': '18.0.1.0.1',
    'category': 'Xportem/Project',
    'summary': 'Extensions for procurement: samples tracking and contracts management',
    'description': """
Xportem Project Extension
========================

This module extends xportem_project with additional features:

Samples Management:
------------------
* Complete sample tracking from request to delivery
* Multiple shipping methods and locations
* Sample quotations and payment tracking
* Configurable status checklist
* Tracking reports
* Bulk sample creation wizard

Contracts and Invoices:
----------------------
* Contract document management
* Invoice tracking
* Integration with selected suppliers
* Contract summary reports

Key Features:
-------------
* Configurable sample statuses
* Multi-location tracking
* Payment status for samples
* Contract lifecycle management
* Document attachments
* PDF reports
* Security groups
* Automated overdue checks
    """,
    'author': 'Xportem',
    'website': 'https://www.xportem.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'xportem_base',
        'xportem_project',
    ],
    'data': [
        'security/procurement_security.xml',
        'security/ir.model.access.csv',
        'data/sample_sequence_data.xml',
        'data/procurement_sample_data.xml',
        'data/cron_data.xml',
        'views/procurement_sample_status_views.xml',
        'views/procurement_shipping_method_views.xml',
        'views/procurement_sample_location_views.xml',
        'views/project_task_sample_views.xml',
        'views/project_task_contract_views.xml',
        'views/project_task_views.xml',
        'wizard/project_task_sample_wizard_views.xml',
        'report/sample_tracking_report.xml',
        'report/contract_report.xml',
        'views/xportem_project_extension_menus.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 4,
}