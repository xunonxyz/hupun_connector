from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductCategory(models.Model):
    _inherit = 'product.category'

    hupun_category_id = fields.Char(string='Hupun Category ID', help="Category ID in Hupun ERP")
    is_hupun_synced = fields.Boolean(string='Synced with Hupun', default=False)

    def action_pull_category_from_hupun(self):
        """
        Try to find this category in Hupun by name and link it.
        """
        self.ensure_one()
        client = self.env['hupun.api']
        
        # Hupun category query usually returns a tree or list.
        # erp/goods/catagorypage/query/v2 supports paging.
        # We might need to search. If the API doesn't support filtering by name, 
        # we might have to fetch all and search in python (expensive if many categories).
        # Assuming we can filter or we just fetch page 1.
        
        # Based on typical Hupun API, it might not support name filter directly in this endpoint.
        # Let's try fetching and matching.
        
        response = client.goods_category_query({'page_no': 1, 'page_size': 100})
        
        data = response.get('data')
        if isinstance(data, dict) and 'list' in data:
            items = data['list']
        elif isinstance(data, list):
            items = data
        else:
            items = []
            
        # Simple matching by name
        found = None
        for item in items:
            if item.get('category_name') == self.name:
                found = item
                break
        
        if not found:
             # If not found in first page, maybe warn user or implement full crawl (not recommended for simple action)
             raise UserError(_("Category '%s' not found in the first 100 categories of Hupun.") % self.name)
             
        self.hupun_category_id = found.get('category_id')
        self.is_hupun_synced = True
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync Successful',
                'message': f"Linked to Hupun Category ID: {self.hupun_category_id}",
                'type': 'success',
                'sticky': False,
            }
        }
