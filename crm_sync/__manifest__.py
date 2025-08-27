{
    'name': 'CRM Synchronization',
    'version': '16.5',
    'summary': 'Sync CRM leads between Odoo Community and Enterprise',
    'description': 'Bidirectional synchronization of CRM leads between two Odoo instances',
    'author': 'Marwah Adel',
    'depends': ['crm', 'sales_team','kw_api','kw_api_custom_endpoint', 'mail', 'hr'],
    'data': [
        # 'views/lead.xml',
        'views/config.xml',
        'security/ir.model.access.csv',
        "views/res_users_views.xml",
        'views/external.xml',
    ],
    'installable': True,
    'application': False,
}