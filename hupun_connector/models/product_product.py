# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = ['product.product']
    
    is_hupun_synced = fields.Boolean(string='Synced from Hupun', default=False)

    def action_push_to_hupun(self):
        """
        Push product to Hupun (add or update).
        """
        client = self.env['hupun.api']
        
        # Create sync log
        log = self.env['hupun.sync.log'].create({
            'name': _('Product Push to Hupun'),
            'sync_type': 'product',
            'start_time': fields.Datetime.now(),
            'status': 'running',
        })
        
        success_count = 0
        fail_count = 0
        details = []
        
        for product in self:
            
            if not product.default_code:
                fail_count += 1
                details.append(f"Skipped {product.name}: No default_code")
                continue
            
            params = {
                'item': {
                    'item_code': product.default_code,
                    'item_name': product.name,
                    'bar_code': product.barcode or '',
                    'sale_price': str(product.list_price),
                }
            }
            
            try:
                # Check existence
                exists = False
                q_resp = client.goods_query({'item_code': product.default_code, 'limit': 1, 'page': 1})
                if q_resp and q_resp.get('data'):
                    data = q_resp['data']
                    if isinstance(data, dict) and data.get('list'):
                        exists = True
                    elif isinstance(data, list) and len(data) > 0:
                        exists = True
                
                if exists:
                    result = client.goods_update(params)
                    if not result or result.get('code') != 0:
                        fail_count += 1
                        details.append(f"Failed to update {product.default_code}: {result}")
                        continue
                else:
                    result = client.goods_add(params)
                    if not result or result.get('code') != 0:
                        fail_count += 1
                        details.append(f"Failed to add {product.default_code}: {result}")
                        continue
                    
                product.is_hupun_synced = True
                success_count += 1
                details.append(f"Synced {product.default_code} successfully")
                
            except Exception as e:
                _logger.error("Failed to sync product %s: %s", product.default_code, e)
                fail_count += 1
                details.append(f"Error syncing {product.default_code}: {str(e)}")
        
        # Update sync log
        log.write({'details': '\n'.join(details)})
        if fail_count == 0:
            log.mark_success(f"Synced {success_count} products successfully")
        elif success_count == 0:
            log.mark_failed(f"All {fail_count} products failed to sync")
        else:
            log.write({
                'status': 'partial',
                'end_time': fields.Datetime.now(),
                'summary': f"Synced {success_count} products, {fail_count} failed"
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sync Complete'),
                'message': _('Synced %d products, %d failed.') % (success_count, fail_count),
                'type': 'success' if fail_count == 0 else 'warning',
                'sticky': False,
            }
        }

    @api.model
    def cron_sync_products_to_hupun(self):
        """
        Cron job to sync products to Hupun.
        """
        products = self.search([('default_code', '!=', False)])
        products.action_push_to_hupun()
