from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json

class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = ['purchase.order', 'hupun.mixin']

    hupun_id = fields.Char(string='Hupun Purchase ID')

    def _get_hupun_data(self):
        # Implement if there is a query interface for purchase bills
        # For now, we might just use it for status sync if available
        # client.purchase_query might be for the old interface, let's check if there is a bill query
        # Assuming purchase_query works for now or we leave it implemented but might fail if IDs don't match types
        return None

    def action_push_purchase_to_hupun(self):
        """
        Push purchase order to Hupun (erp/purchase/purchasebill/add).
        """
        self.ensure_one()
        
        if self.hupun_id:
             raise UserError(_("This order is already synced with Hupun (ID: %s).") % self.hupun_id)

        if not self.partner_id.hupun_supplier_id:
            raise UserError(_("Supplier must be synced with Hupun first."))
            
        warehouse = self.picking_type_id.warehouse_id
        if not warehouse.hupun_storage_code and not warehouse.code:
             raise UserError(_("Warehouse must have a code or be synced with Hupun."))
        
        storage_code = warehouse.hupun_storage_code or warehouse.code

        details = []
        for line in self.order_line:
            product = line.product_id
            # Prefer hupun_spec_code (variant), then hupun_goods_code (template), then internal reference
            sku_code = product.hupun_spec_code or product.hupun_goods_code or product.default_code
            
            if not sku_code:
                raise UserError(_("Product %s has no SKU code (Internal Reference or Hupun Code).") % product.name)
                
            details.append({
                'sku_code': sku_code,
                'quantity': line.product_qty,
                'price': line.price_unit,
                'remark': line.name,
            })

        if not details:
            raise UserError(_("No lines to push."))

        params = {
            'bill_date': self.date_order.strftime('%Y-%m-%d %H:%M:%S'),
            'supplier_id': self.partner_id.hupun_supplier_id,
            'storage_code': storage_code,
            'remark': self.notes or '',
            'details': json.dumps(details) # API usually expects JSON string for complex lists in form data
        }
        
        # Some APIs might take 'details' as a list if sending JSON body, 
        # but Hupun often uses form-data where lists need to be JSON strings or specific format.
        # Based on previous experience with Hupun/WanliNiu, complex structures often need JSON stringification 
        # if the content-type is not application/json. 
        # However, the `make_request` uses `requests.post(data=params)`.
        # Let's try sending as list first if the library handles it, or check documentation.
        # Documentation says "details" is "json array". In form-data, usually means string.
        
        client = self.env['hupun.api']
        response = client.purchase_bill_add(params)
        
        # Response: {"data": "bill_no", ...}
        data = response.get('data')
        if data:
            self.hupun_id = str(data)
            self.hupun_status = 'Created' # Initial status
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Push Successful',
                'message': 'Purchase Order added to Hupun.',
                'type': 'success',
                'sticky': False,
            }
        }
