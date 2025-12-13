from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    hupun_storage_code = fields.Char(string='Hupun Storage Code', copy=False, help="Storage Code in Hupun ERP")
    is_hupun_synced = fields.Boolean(string='Synced with Hupun', default=False)

    def action_push_storage_to_hupun(self):
        """
        Push warehouse to Hupun (erp/base/storage/add).
        """
        self.ensure_one()
        if not self.code:
            raise UserError(_("Warehouse Code is required."))

        client = self.env['hupun.api']
        
        # Construct parameters
        # Hupun usually requires storage_code and storage_name
        params = {
            'storage_code': self.code,
            'storage_name': self.name,
            'contact': self.partner_id.name if self.partner_id else '',
            'mobile': self.partner_id.mobile or self.partner_id.phone or '',
            'address': self.partner_id.contact_address or '',
            # 'province': ..., 'city': ..., 'district': ... # If we have structured address
        }
        
        if self.hupun_storage_code:
             raise UserError(_("This warehouse is already synced with Hupun (Code: %s).") % self.hupun_storage_code)

        # Check if it already exists in Hupun to avoid duplication error if we just missed the link
        # But for "add" action, we assume user wants to create. 
        # If it fails because it exists, Hupun API usually returns an error message.
        
        response = client.storage_add(params)
        
        # If success, we assume the code we sent is the code in Hupun
        self.hupun_storage_code = self.code
        self.is_hupun_synced = True
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Push Successful',
                'message': 'Warehouse added to Hupun.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_pull_storage_from_hupun(self):
        """
        Link warehouse with Hupun by Code.
        """
        self.ensure_one()
        client = self.env['hupun.api']
        
        if not self.code:
            raise UserError(_("Warehouse Code is required to sync."))
            
        # Query by storage_code
        response = client.storage_query({'storage_code': self.code})
        data = response.get('data')
        
        if isinstance(data, dict) and 'list' in data:
            items = data['list']
        elif isinstance(data, list):
            items = data
        else:
            items = []
            
        if not items:
            raise UserError(_("Warehouse not found in Hupun with code %s.") % self.code)
            
        # If found, link it
        self.hupun_storage_code = self.code
        self.is_hupun_synced = True
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync Successful',
                'message': 'Warehouse linked with Hupun.',
                'type': 'success',
                'sticky': False,
            }
        }
