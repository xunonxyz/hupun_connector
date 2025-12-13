from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hupun_goods_code = fields.Char(string='Hupun Goods Code', help="Code of the goods in Hupun ERP")
    is_hupun_synced = fields.Boolean(string='Synced from Hupun', default=False)
    
    # Package/Bundle fields
    is_hupun_package = fields.Boolean(string='Is Hupun Package', default=False)
    hupun_package_line_ids = fields.One2many('hupun.package.line', 'template_id', string='Package Content')

    def action_sync_from_hupun(self):
        """
        Pull product details from Hupun based on the Internal Reference (default_code) 
        matching Hupun's goods_code.
        """
        self.ensure_one()
        if not self.default_code:
            raise UserError(_("Please set an Internal Reference to sync with Hupun."))

        client = self.env['hupun.api']
        # Use the new wrapper method
        response = client.goods_query({
            'goods_code': self.default_code,
            'page_no': 1,
            'page_size': 1
        })

        # Parse response - this depends on actual Hupun response structure
        # Usually response['data'] is a list or response['data']['list']
        # Let's assume a standard structure for now and add error handling if it fails
        
        data = response.get('data')
        if not data:
             raise UserError(_("No data received from Hupun."))
             
        # Handle pagination wrapper if exists
        if isinstance(data, dict) and 'list' in data:
            items = data['list']
        elif isinstance(data, list):
            items = data
        else:
            items = []

        if not items:
            raise UserError(_("Product not found in Hupun with code %s") % self.default_code)

        item = items[0]
        self.write({
            'name': item.get('goods_name', self.name),
            'hupun_goods_code': item.get('goods_code'),
            'is_hupun_synced': True,
        })
        
        # Handle variants (specs) if necessary
        # This is complex because Odoo variants are generated from attributes.
        # For simple sync, we might just update the main template info.
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync Successful',
                'message': 'Product details updated from Hupun.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_push_package_to_hupun(self):
        """
        Push product as a package to Hupun (erp/goods/add/goodspackage).
        """
        self.ensure_one()
        if not self.is_hupun_package:
            raise UserError(_("This product is not marked as a Hupun Package."))
            
        if not self.default_code:
            raise UserError(_("Internal Reference (Code) is required."))
            
        if not self.hupun_package_line_ids:
            raise UserError(_("Package content is empty."))

        client = self.env['hupun.api']
        
        details = []
        for line in self.hupun_package_line_ids:
            product = line.product_id
            sku_code = product.hupun_spec_code or product.hupun_goods_code or product.default_code
            
            if not sku_code:
                raise UserError(_("Product %s in package has no SKU code.") % product.name)
                
            details.append({
                'sku_code': sku_code,
                'count': line.quantity, # API usually uses 'count' or 'quantity'
            })
            
        params = {
            'package_code': self.default_code,
            'package_name': self.name,
            'details': json.dumps(details)
        }
        
        client.goods_package_add(params)
        
        self.is_hupun_synced = True
        self.hupun_goods_code = self.default_code
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Push Successful',
                'message': 'Package added to Hupun.',
                'type': 'success',
                'sticky': False,
            }
        }

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    hupun_spec_code = fields.Char(string='Hupun Spec Code')

class HupunPackageLine(models.Model):
    _name = 'hupun.package.line'
    _description = 'Hupun Package Line'
    
    template_id = fields.Many2one('product.template', string='Product Template', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
