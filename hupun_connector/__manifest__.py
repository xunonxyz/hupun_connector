{
    'name': 'Hupun Connector',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Integration with Hupun ERP (Wanli Niu)',
    'description': """
        This module allows integration with Hupun ERP (Wanli Niu).
        It provides configuration for API credentials and a base client for making API requests.
    """,
    'author': 'Your Name',
    'depends': ['base', 'sale_management', 'stock', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/product_views.xml',
        'views/product_category_views.xml',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'views/stock_warehouse_views.xml',
        'views/stock_picking_views.xml',
        'views/purchase_order_views.xml',
        'views/hupun_platform_bill_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
