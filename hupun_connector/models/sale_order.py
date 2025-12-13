from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'hupun.mixin']

    hupun_id = fields.Char(string='Hupun Trade ID')

    def _get_hupun_data(self):
        client = self.env['hupun.api']
        response = client.trade_query({
            'trade_id': self.hupun_id,
            'page_no': 1,
            'page_size': 1
        })
        
        data = response.get('data')
        if isinstance(data, dict) and 'list' in data:
            items = data['list']
        elif isinstance(data, list):
            items = data
        else:
            items = []
            
        return items[0] if items else None
