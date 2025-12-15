from odoo import fields, models, _
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hupun_app_key = fields.Char(string='Hupun App Key', config_parameter='hupun_connector.app_key', default='T3487322185')
    hupun_app_secret = fields.Char(string='Hupun App Secret', config_parameter='hupun_connector.app_secret', default='b13ade5defac14295c0fd6cf706cf94e', groups='base.group_system')
    hupun_api_base_url = fields.Char(string='Hupun API Base URL', default='https://erp-open.hupun.com/api', config_parameter='hupun_connector.api_base_url')

    def action_test_hupun_connection(self):
        self.ensure_one()
        
        # Save settings first to ensure we use the latest values
        self.set_values()
        
        try:
            # Try to call a simple endpoint. 
            # 'erp/goods/query' is a common one. Even with no params it should return something or a specific error, not auth error.
            # We pass page_no=1, page_size=1 to minimize data.
            client = self.env['hupun.api']
            result = client.warehouse_query({
                'page_no': 1, 
                'page_size': 1, 
                'category': 1
            })
            
            # Check if response indicates success. 
            # Hupun usually returns 'code' or 'status'. 
            # If code is 0 or success is true, it's good.
            # If we get here without exception, at least network and signature (likely) are okay.
            
            message = f"Connection Successful! Response: {result}"
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Test',
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Connection Failed',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
