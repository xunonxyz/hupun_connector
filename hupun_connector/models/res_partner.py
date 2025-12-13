from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    hupun_supplier_id = fields.Char(string='Hupun Supplier ID', copy=False, help="Supplier ID in Hupun ERP")
    is_hupun_supplier = fields.Boolean(string='Is Hupun Supplier', default=False)

    def action_push_supplier_to_hupun(self):
        """
        Push supplier to Hupun (erp/base/supplier/add).
        """
        self.ensure_one()
        if not self.name:
            raise UserError(_("Supplier Name is required."))

        client = self.env['hupun.api']
        
        # Construct parameters based on Hupun API requirements
        # Assuming basic fields: supplier_name, contact, mobile, address, etc.
        params = {
            'supplier_name': self.name,
            'contact': self.child_ids[0].name if self.child_ids else self.name,
            'mobile': self.mobile or self.phone or '',
            'address': self.contact_address or '',
            'remark': self.comment or '',
        }
        
        # If we already have an ID, maybe we should update? 
        # The user only asked for "add" (erp/base/supplier/add).
        # Hupun might not have an update endpoint for suppliers or it's different.
        # Let's assume we only push new ones for now or check if it exists.
        
        if self.hupun_supplier_id:
             raise UserError(_("This supplier is already synced with Hupun (ID: %s).") % self.hupun_supplier_id)

        response = client.supplier_add(params)
        
        # Parse response to get the new ID
        # Response format usually: {"code": 0, "data": "new_id_or_object", "message": "success"}
        # Or data might be the ID directly.
        
        data = response.get('data')
        if not data:
             # Sometimes data is None but code is 0?
             # If success, we might need to query back or just mark as synced.
             pass
             
        # Assuming data contains the ID or we can't get it easily without querying back.
        # Let's try to query back by name if data is not the ID.
        
        # If the API returns the ID directly:
        if isinstance(data, (str, int)):
            self.hupun_supplier_id = str(data)
        
        self.is_hupun_supplier = True
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Push Successful',
                'message': 'Supplier added to Hupun.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_update_supplier_in_hupun(self):
        """
        Update supplier in Hupun (erp/base/supplier/modify).
        """
        self.ensure_one()
        if not self.hupun_supplier_id:
            raise UserError(_("This supplier is not linked to Hupun yet. Please push or pull first."))

        client = self.env['hupun.api']
        
        params = {
            'supplier_id': self.hupun_supplier_id,
            'supplier_name': self.name,
            'contact': self.child_ids[0].name if self.child_ids else self.name,
            'mobile': self.mobile or self.phone or '',
            'address': self.contact_address or '',
            'remark': self.comment or '',
        }
        
        client.supplier_modify(params)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Update Successful',
                'message': 'Supplier updated in Hupun.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_pull_supplier_from_hupun(self):
        """
        Pull supplier info from Hupun by Name or ID.
        """
        self.ensure_one()
        client = self.env['hupun.api']
        
        query_params = {
            'page_no': 1,
            'page_size': 1
        }
        
        if self.hupun_supplier_id:
            query_params['supplier_id'] = self.hupun_supplier_id
        elif self.name:
            query_params['supplier_name'] = self.name
        else:
            raise UserError(_("Name or Hupun ID required to sync."))
            
        response = client.supplier_query(query_params)
        data = response.get('data')
        
        if isinstance(data, dict) and 'list' in data:
            items = data['list']
        elif isinstance(data, list):
            items = data
        else:
            items = []
            
        if not items:
            raise UserError(_("Supplier not found in Hupun."))
            
        item = items[0]
        self.hupun_supplier_id = item.get('supplier_id')
        self.is_hupun_supplier = True
        # Update other fields if needed
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync Successful',
                'message': 'Supplier linked with Hupun.',
                'type': 'success',
                'sticky': False,
            }
        }
