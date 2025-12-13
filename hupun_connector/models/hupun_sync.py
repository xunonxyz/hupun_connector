from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HupunSync(models.TransientModel):
    _name = 'hupun.sync'
    _description = 'Hupun Synchronization Wizard'

    sync_type = fields.Selection([
        ('product', 'Products'),
        ('order', 'Orders'),
        ('stock', 'Stock'),
    ], string='Sync Type', required=True, default='product')
    
    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='End Date', default=fields.Datetime.now)

    def action_sync(self):
        self.ensure_one()
        if self.sync_type == 'product':
            return self.sync_products()
        elif self.sync_type == 'order':
            return self.sync_orders()
        elif self.sync_type == 'stock':
            return self.sync_stock()

    def sync_products(self):
        # Placeholder for product sync logic
        raise UserError(_("Product synchronization is not yet implemented."))

    def sync_orders(self):
        # Placeholder for order sync logic
        raise UserError(_("Order synchronization is not yet implemented."))

    def sync_stock(self):
        # Placeholder for stock sync logic
        raise UserError(_("Stock synchronization is not yet implemented."))
