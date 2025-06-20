# __manifest__.py (minimal test)
{
    'name': 'Xportem Project Extension',
    'version': '18.0.1.0.1',
    'depends': ['base', 'mail', 'xportem_base', 'xportem_project'],
    'data': [
        # Test 1: Only security
        'security/procurement_security.xml',
        'security/ir.model.access.csv',
    ],
}