# -*- coding: utf-8 -*-

import json
import logging
import time
from odoo import models, api, _
from odoo.exceptions import UserError
from . import hupun_endpoints
from .hupun_request import Request


_logger = logging.getLogger(__name__)

class HupunAPI(models.AbstractModel):
    _name = 'hupun.api'
    _description = 'Hupun API Client'

    def get_client(self):
        """Returns an instance of the client with credentials loaded."""
        return self

    def _get_credentials(self):
        ICP = self.env['ir.config_parameter'].sudo()
        app_key = ICP.get_param('hupun_connector.app_key')
        app_secret = ICP.get_param('hupun_connector.app_secret')
        base_url = ICP.get_param('hupun_connector.api_base_url', 'https://open-api.hupun.com/api')
        
        if not app_key or not app_secret:
            raise UserError(_("Hupun App Key and App Secret must be configured in settings."))
            
        return app_key.strip(), app_secret.strip(), base_url.strip()

    def make_request(self, endpoint, params=None, method='POST'):
        """
        Makes a request to the Hupun API using the official Request class.
        :param endpoint: API endpoint (e.g., 'erp/goods/query')
        :param params: Dictionary of business parameters
        :param method: HTTP method (default POST) - Note: Request class only supports POST
        :return: JSON response
        """
        app_key, app_secret, base_url = self._get_credentials()
        
        if params is None:
            params = {}
            
        # Initialize the official Request class
        # Note: base_url usually includes /api, but Request class adds it if missing.
        # If base_url is https://erp-open.hupun.com/api, Request class handles it.
        req = Request(base_url, app_key, app_secret)
        
        try:
            # Execute request
            # The Request.request method returns the response text
            response_text = req.request(endpoint, params)
            
            if not response_text:
                 raise UserError(_("Empty response from Hupun API."))
            
            result = json.loads(response_text)
            
            _logger.info(f"Hupun API Response: {result}")
            
            return result
            
        except Exception as e:
            _logger.error(f"Hupun API Request Failed: {e}")
            raise UserError(_("Failed to connect to Hupun API: %s") % str(e))

    # --- Base Info API (基础信息接口) ---
    def shop_query(self, params=None):
        """Query shop information (erp/base/shop/page/get)"""
        return self.make_request(hupun_endpoints.SHOP_QUERY, params)

    def supplier_query(self, params=None):
        """Query supplier information (erp/base/supplier/query)"""
        return self.make_request(hupun_endpoints.SUPPLIER_QUERY, params)

    def supplier_add(self, params):
        """Add supplier (erp/base/supplier/add)"""
        return self.make_request(hupun_endpoints.SUPPLIER_ADD, params)

    def supplier_modify(self, params):
        """Modify supplier (erp/base/supplier/modify)"""
        return self.make_request(hupun_endpoints.SUPPLIER_MODIFY, params)

    def storage_query(self, params=None):
        """Query storage/warehouse information (erp/base/storage/query)"""
        return self.make_request(hupun_endpoints.STORAGE_QUERY, params)

    def storage_add(self, params):
        """Add storage/warehouse (erp/base/storage/add)"""
        return self.make_request(hupun_endpoints.STORAGE_ADD, params)

    def distr_com_query(self, params=None):
        """Query distribution company (erp/base/distr/com/page/get)"""
        return self.make_request(hupun_endpoints.DISTR_COM_QUERY, params)
    
    # /erp/base/shop/offline/add
    def shop_offline_add(self, params):
        """Add offline shop (erp/base/shop/offline/add)"""
        return self.make_request('erp/base/shop/offline/add', params)
    
    # /erp/base/custom/offline/add
    def custom_offline_add(self, params):
        """Add offline customer (erp/base/custom/offline/add)"""
        return self.make_request('erp/base/custom/offline/add', params)

    # --- Inventory API (库存接口) ---
    def inventory_query(self, params=None):
        """Query inventory (erp/stock/query)"""
        return self.make_request(hupun_endpoints.INVENTORY_QUERY, params)
        
    def inventory_sync(self, params):
        """Sync inventory quantity (erp/stock/sync)"""
        return self.make_request(hupun_endpoints.INVENTORY_SYNC, params)

    def batch_query_by_bill(self, params):
        """Query batch info by bill code (erp/batch/billbatch)"""
        return self.make_request(hupun_endpoints.BATCH_QUERY_BY_BILL, params)
    
    #  ---订单 --
    # /erp/opentrade/list/trades
    def order_list_trades(self, params=None):
        """List open trades/orders (erp/opentrade/list/trades)"""
        return self.make_request('erp/opentrade/list/trades', params)
    
    # /erp/opentrade/modify/address
    def order_modify_address(self, params):
        """Modify order address (erp/opentrade/modify/address)"""
        return self.make_request('erp/opentrade/modify/address', params)
    
    # /erp/opentrade/modify/express
    def order_modify_express(self, params):
        """Modify order express info (erp/opentrade/modify/express)"""
        return self.make_request('erp/opentrade/modify/express', params)
    
    # /erp/opentrade/modify/mark
    def order_modify_mark(self, params):
        """Modify order mark/note (erp/opentrade/modify/mark)"""
        return self.make_request('erp/opentrade/modify/mark', params)
    
    # /erp/opentrade/modify/remark
    def order_modify_remark(self, params):
        """Modify order remark (erp/opentrade/modify/remark)"""
        return self.make_request('erp/opentrade/modify/remark', params)
    
    # /erp/opentrade/send/trades
    def order_send_trades(self, params):
        """Send trades/orders (erp/opentrade/send/trades)"""
        return self.make_request('erp/opentrade/send/trades', params)
    
    # /erp/opentrade/trade/commit
    def order_trade_commit(self, params):
        """Commit trade/order (erp/opentrade/trade/commit)"""
        return self.make_request('erp/opentrade/trade/commit', params)
    
    # /erp/opentrade/trade/exception/commit
    def order_trade_exception_commit(self, params):
        """Commit trade/order exception (erp/opentrade/trade/exception/commit)"""
        return self.make_request('erp/opentrade/trade/exception/commit', params)
    
    # /erp/sale/stock/out/add
    def sale_stock_out_add(self, params):
        """Add sale stock out (erp/sale/stock/out/add)"""
        return self.make_request('erp/sale/stock/out/add', params)\
    
    # /erp/sale/stock/out/query
    def sale_stock_out_query(self, params=None):
        """Query sale stock out (erp/sale/stock/out/query)"""
        return self.make_request('erp/sale/stock/out/query', params)
    
    # /erp/logistic/trace/list
    def logistic_trace_list(self, params=None):
        """List logistic trace (erp/logistic/trace/list)"""
        return self.make_request('erp/logistic/trace/list', params)
    
    # /erp/opentrade/trade/commit/by_goods
    def order_trade_commit_by_goods(self, params):
        """Commit trade/order by goods (erp/opentrade/trade/commit/by_goods)"""
        return self.make_request('erp/opentrade/trade/commit/by_goods', params)

    # --- Goods API (商品接口) ---
    def goods_query(self, params=None):
        """Query goods information (/erp/goods/spec/open/query/goodswithspeclist)"""
        return self.make_request(hupun_endpoints.GOODS_QUERY, params)

    def goods_add(self, params):
        """Add new goods (erp/goods/add)"""
        return self.make_request(hupun_endpoints.GOODS_ADD, params)

    def goods_update(self, params):
        """Update goods information (erp/goods/update)"""
        return self.make_request(hupun_endpoints.GOODS_UPDATE, params)
        
    def goods_sku_query(self, params=None):
        """Query goods SKU (erp/goods/sku/query)"""
        return self.make_request(hupun_endpoints.GOODS_SKU_QUERY, params)

    def goods_package_add(self, params):
        """Add goods package/bundle (erp/goods/add/goodspackage)"""
        return self.make_request(hupun_endpoints.GOODS_PACKAGE_ADD, params)

    def goods_category_query(self, params=None):
        """Query goods categories (erp/goods/catagorypage/query/v2)"""
        return self.make_request(hupun_endpoints.GOODS_CATEGORY_QUERY, params)

    # --- Trade API (订单接口) ---
    def trade_query(self, params=None):
        """Query trades/orders (erp/trade/query)"""
        return self.make_request(hupun_endpoints.TRADE_QUERY, params)

    def trade_open_query(self, params=None):
        """Query open trades/orders (erp/opentrade/list/trades)"""
        return self.make_request(hupun_endpoints.TRADE_OPEN_QUERY, params)

    def trade_add(self, params):
        """Add new trade (erp/trade/add)"""
        return self.make_request(hupun_endpoints.TRADE_ADD, params)
        
    def trade_delivery(self, params):
        """Trade delivery/shipping (erp/trade/delivery)"""
        return self.make_request(hupun_endpoints.TRADE_DELIVERY, params)

    # --- Purchase API (采购接口) ---
    def purchase_query(self, params=None):
        """Query purchase orders (erp/purchase/query)"""
        return self.make_request(hupun_endpoints.PURCHASE_QUERY, params)

    def purchase_add(self, params):
        """Add purchase order (erp/purchase/add)"""
        return self.make_request(hupun_endpoints.PURCHASE_ADD, params)

    def purchase_bill_add(self, params):
        """Add purchase bill (erp/purchase/purchasebill/add)"""
        return self.make_request(hupun_endpoints.PURCHASE_BILL_ADD, params)

    # --- Finance/BI API (财务/BI接口) ---
    def platform_bill_query(self, params=None):
        """Query platform bills (erp/bi/service/bill/platformbill/querybill)"""
        return self.make_request(hupun_endpoints.PLATFORM_BILL_QUERY, params)

    # --- After Sales API (售后接口) ---
    def refund_query(self, params=None):
        """Query refund/return orders (erp/refund/query)"""
        return self.make_request(hupun_endpoints.REFUND_QUERY, params)

