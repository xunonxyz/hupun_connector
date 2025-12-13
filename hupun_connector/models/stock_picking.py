from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    hupun_bill_code = fields.Char(string='Hupun Bill Code', copy=False, help="Bill Code in Hupun ERP")
    hupun_bill_type = fields.Selection([
        ('1', 'Purchase In'),
        ('2', 'Purchase Return'),
        ('3', 'Transfer In'),
        ('4', 'Transfer Out'),
        ('5', 'Other In'),
        ('6', 'Other Out'),
        ('7', 'Sales Out'),
        ('8', 'After-sales Return'),
        ('9', 'Offline Sales Out'),
        ('10', 'Finished Product In'),
        ('11', 'Finished Product Cancel'),
        ('12', 'Online Sales Order'),
        ('13', 'Inventory Adjustment'),
    ], string='Hupun Bill Type', help="Type of the bill in Hupun")

    def action_query_hupun_batch(self):
        """
        Query batch info from Hupun based on bill code and type.
        """
        self.ensure_one()
        if not self.hupun_bill_code:
            raise UserError(_("Hupun Bill Code is required."))
        if not self.hupun_bill_type:
            raise UserError(_("Hupun Bill Type is required."))

        client = self.env['hupun.api']
        response = client.batch_query_by_bill({
            'code': self.hupun_bill_code,
            'type': int(self.hupun_bill_type)
        })
        
        data = response.get('data')
        if not data:
             raise UserError(_("No batch information found."))
             
        # Format the result for display
        message = "Batch Info:\n"
        for item in data:
            sku = item.get('sku_code', 'N/A')
            batches = item.get('batchs', [])
            if batches:
                batch_info = ", ".join([str(b) for b in batches])
                message += f"SKU: {sku}, Batches: {batch_info}\n"
            else:
                message += f"SKU: {sku}, No specific batch info.\n"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Batch Info',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }
