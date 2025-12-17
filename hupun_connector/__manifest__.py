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
        'security/hupun_security.xml',
        'security/ir.model.access.csv',

        'data/ir_cron_data.xml',

        'views/res_config_settings_views.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
        'views/hupun_sync_log_views.xml',
        'views/hupun_menus.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
