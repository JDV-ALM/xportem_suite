# -*- coding: utf-8 -*-
{
    'name': 'Xportem Procurement Dashboards',
    'version': '18.0.1.0.0',
    'category': 'Xportem/Dashboards',
    'summary': 'Dashboards for daily procurement tracking and analysis',
    'description': """
Xportem Procurement Dashboards
==============================

This module provides comprehensive dashboards for procurement management:

Main Features:
--------------
* Daily Procurement Dashboard
  - KPIs for new requests, active tasks, pending quotations
  - Urgent requests monitoring
  - Samples in transit tracking

* Quotations Analysis Dashboard
  - Supplier performance analysis
  - Price comparison matrices
  - Lead time analytics
  - Pending quotations alerts

* Samples & Shipments Tracking
  - Real-time location tracking
  - Overdue alerts
  - Payment status monitoring
  - Visual timeline of shipments

Key Benefits:
-------------
* Real-time visibility of procurement operations
* Quick identification of bottlenecks
* Supplier performance comparison
* Automated alerts for critical items
* KISS principle: Simple, focused, effective

Technical Details:
------------------
* Uses Odoo 18 spreadsheet framework
* Dynamic data with PIVOT formulas
* Conditional formatting for alerts
* Global filters for date ranges and suppliers
* Mobile-responsive design
    """,
    'author': 'Xportem',
    'website': 'https://www.xportem.com',
    'license': 'LGPL-3',
    'depends': [
        'spreadsheet_dashboard',
        'xportem_project',
        'xportem_project_extension',
    ],
    'data': [
        'data/dashboards.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 5,
    'assets': {
        'web.assets_backend': [
            # Add any custom JS/CSS if needed
        ],
    },
}