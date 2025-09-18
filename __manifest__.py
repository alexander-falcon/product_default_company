# -*- coding: utf-8 -*-

{
    'name': "Default Company in Product",
    'version': '16.0.1.0',
    'category': 'Product',
    'summary': 'Set current company as default in product multi-company field',
    'description': """
        When creating a new product, automatically set the current company
        in the companies field (partner_multi_company module required)
    """,
    'depends': ['product_multi_company'],
    'data': [
        'security/ir.model.access.csv',
     
    ],
    'qweb': [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'author': "Alexander Falcon",
    # 'website': "http://www.yourcompany.com",
    'license': 'LGPL-3',
}
