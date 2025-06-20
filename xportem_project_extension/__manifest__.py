# __manifest__.py (minimal test)
{
    'name': 'Xportem Project Extension',
    'version': '18.0.1.0.1',
    'depends': ['base', 'mail', 'xportem_base', 'xportem_project'],
    'data': [
        'security/procurement_security.xml',
        'security/ir.model.access.csv',
        'data/sample_sequence_data.xml',
],
}