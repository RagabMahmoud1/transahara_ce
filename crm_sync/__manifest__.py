{
    'name': 'CRM Synchronization',
    'version': '16.0',
    'summary': 'Sync CRM leads between Odoo Community and Enterprise',
    'description': 'Bidirectional synchronization of CRM leads between two Odoo instances',
    'author': 'Marwah Adel',
    'depends': ['crm','kw_api','kw_api_custom_endpoint', 'mail', 'hr'],
    'data': [
        'views/lead.xml',
        'views/config.xml'
    ],
    'installable': True,
    'application': False,
}