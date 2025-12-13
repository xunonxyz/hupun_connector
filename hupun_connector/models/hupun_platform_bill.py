from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HupunPlatformBill(models.Model):
    _name = 'hupun.platform.bill'
    _description = 'Hupun Platform Bill'
    _order = 'bill_date desc'

    bill_no = fields.Char(string='Bill No', required=True, index=True)
    bill_date = fields.Datetime(string='Bill Date')
    shop_name = fields.Char(string='Shop Name')
    amount = fields.Float(string='Amount')
    currency = fields.Char(string='Currency')
    bill_type = fields.Char(string='Bill Type')
    remark = fields.Text(string='Remark')
    
    # Raw data storage for fields we might not have mapped
    raw_data = fields.Text(string='Raw Data')

    def action_fetch_bills(self):
        """
        Fetch bills from Hupun.
        This is a basic implementation. In production, you'd want date filters.
        """
        client = self.env['hupun.api']
        
        # Example params, usually need start/end time
        # Hupun API usually requires time range
        import datetime
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(days=1)
        
        params = {
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'page_no': 1,
            'page_size': 50
        }
        
        response = client.platform_bill_query(params)
        
        data = response.get('data')
        if isinstance(data, dict) and 'list' in data:
            items = data['list']
        elif isinstance(data, list):
            items = data
        else:
            items = []
            
        if not items:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Fetch Complete',
                    'message': 'No new bills found.',
                    'type': 'info',
                    'sticky': False,
                }
            }

        count = 0
        for item in items:
            bill_no = item.get('bill_no') or item.get('id') # Adjust based on actual response
            if not bill_no:
                continue
                
            existing = self.search([('bill_no', '=', bill_no)], limit=1)
            if existing:
                continue
                
            self.create({
                'bill_no': bill_no,
                'bill_date': item.get('bill_date') or item.get('create_time'),
                'shop_name': item.get('shop_name'),
                'amount': item.get('amount') or item.get('total_amount'),
                'currency': item.get('currency', 'CNY'),
                'bill_type': item.get('bill_type'),
                'remark': item.get('remark'),
                'raw_data': str(item)
            })
            count += 1
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Fetch Complete',
                'message': f"Fetched {count} new bills.",
                'type': 'success',
                'sticky': False,
            }
        }
