# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order']

    express_code = fields.Char(string='Hupun Tracking No')
    hupun_actual_payment = fields.Float(string='Hupun Actual Payment')

    def action_sync_hupun_orders(self):
        """
        Manual action to sync data for this specific order from Hupun.
        """
        self.cron_sync_hupun_orders()

    @api.model
    def cron_sync_hupun_orders(self):
        """
        Cron job to sync orders from Hupun.
        Fetches orders (specifically looking for shipped ones) and updates Odoo.
        """
        client = self.env['hupun.api']
        SyncLog = self.env['hupun.sync.log']
        
        # Sync statistics
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        detail_logs = []
        
        # Create sync log record
        sync_log = SyncLog.create({
            'name': f'Order Sync {fields.Datetime.now()}',
            'sync_type': 'order',
            'status': 'running',
        })
        
        _logger.info("===== Hupun Order Sync Started =====")
        
        try:
            create_time = fields.Datetime.to_string(fields.Datetime.now() - datetime.timedelta(days=6))
            detail_logs.append(f"Fetching orders created after: {create_time}")
            
            request_data = {
                'limit': 200,
                'page': 1,
                'trade_status': '8',
                'create_time': create_time,
                'query_extend': {
                    'tp_logistics_type': 0,
                }
            }
            response = client.order_list_trades(request_data)
            
            # Store request/response in sync log
            sync_log.write({
                'request_data': str(request_data),
                'response_data': str(response)[:5000],  # Limit response data size
            })

            if response.get('code') != 0:
                error_msg = f"Hupun API error: {response.get('message')}"
                _logger.error(error_msg)
                sync_log.mark_failed(error_msg)
                return
            
            data = response.get('data')
            items = []
            if isinstance(data, dict) and 'list' in data:
                items = data['list']
            elif isinstance(data, list):
                items = data
            
            detail_logs.append(f"Fetched {len(items)} orders from Hupun API")
            _logger.info(f"Fetched {len(items)} orders from Hupun API")
            
            for item in items:
                trade_no = item.get('trade_no')
                if not trade_no:
                    skipped_count += 1
                    detail_logs.append(f"Skipped order with no trade_no")
                    continue

                # Find existing order
                order = self.search([('name', '=', trade_no)], limit=1)

                # Prepare values to sync or create with
                vals = {}
                if 'payment' in item:
                    vals['hupun_actual_payment'] = float(item['payment'])

                express_code = item.get('express_code')
                if express_code:
                    vals['express_code'] = express_code

                # If no order found, attempt to create one with minimal required fields
                if not order:

                    buyer = item.get('buyer')
                    buyer_account = item.get('buyer_account')
                    buyer_name = item.get('buyer_name')
                    buyer_mobile = item.get('buyer_mobile')
                    full_name = f"{buyer_name} ({buyer_account})"
                    
                    partner = False
                    if buyer_mobile:
                        partner = self.env['res.partner'].search([('phone', '=', buyer_mobile)], limit=1)
                    
                    if not partner and full_name:
                        partner = self.env['res.partner'].search([('name', '=', full_name)], limit=1)
                        
                    if not partner:
                        partner_vals = {
                            'name': full_name,
                            'phone': buyer_mobile,
                            'comment': f'Created from Hupun order sync {buyer_account}-{ buyer }-{buyer_name}-{buyer_mobile}',
                        }
                        partner = self.env['res.partner'].create(partner_vals)
                        detail_logs.append(f"Created new partner: {full_name}")

                    create_vals = {
                        'name': trade_no,
                        'partner_id': partner.id,
                    }
                    
                    # Create Order Lines
                    lines_data = item.get('orders') or item.get('details') or []
                    order_lines = []
                    for line in lines_data:
                        sku_code = line.get('sku_code')
                        qty = float(line.get('size', 0))
                        price = float(line.get('price', 0))
                        
                        product = self.env['product.product'].search([('default_code', '=', sku_code)], limit=1)
                        if not product:
                            # create
                            product_vals = {
                                'name': f"{line.get('item_name')} - {line.get('sku_name')}",
                                'default_code': line.get('sku_code'),
                                'barcode': line.get('bar_code'),
                                'list_price': price,
                            }
                            product = self.env['product.product'].create(product_vals)
                            detail_logs.append(f"Created new product: {sku_code}")

                        if product:
                            order_lines.append((0, 0, {
                                'product_id': product.id,
                                'product_uom_qty': qty,
                                'price_unit': price,
                                'name': line.get('title') or product.name,
                            }))
                    
                    if order_lines:
                        create_vals['order_line'] = order_lines

                    create_vals.update(vals)
                    try:
                        order = self.create(create_vals)
                        created_count += 1
                        detail_logs.append(f"Created order {trade_no} with {len(order_lines)} lines")
                    except Exception as e:
                        error_count += 1
                        detail_logs.append(f"Failed to create order {trade_no}: {e}")
                        _logger.error(f"Failed to create Hupun Order {trade_no}: {e}")
                else:
                    # Update existing order
                    if vals:
                        try:
                            order.write(vals)
                            updated_count += 1
                            detail_logs.append(f"Updated order {trade_no}")
                        except Exception as e:
                            error_count += 1
                            detail_logs.append(f"Failed to update order {trade_no}: {e}")
                            _logger.error(f"Failed to update Hupun Order {trade_no}: {e}")
            
            # Determine final status
            if error_count > 0 and (created_count > 0 or updated_count > 0):
                status = 'partial'
            elif error_count > 0:
                status = 'failed'
            else:
                status = 'success'
            
            summary = f"Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}"
            sync_log.write({
                'status': status,
                'end_time': fields.Datetime.now(),
                'summary': summary,
                'details': '\n'.join(detail_logs),
            })
            _logger.info(f"===== Hupun Order Sync Completed: {summary} =====")
                    
        except Exception as e:
            error_msg = f"Error syncing Hupun orders: {e}"
            _logger.error(error_msg)
            sync_log.write({
                'status': 'failed',
                'end_time': fields.Datetime.now(),
                'summary': error_msg,
                'details': '\n'.join(detail_logs),
            })
