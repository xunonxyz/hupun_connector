import hashlib
import time
import urllib.parse
import requests
import json
import logging
from odoo import models, api, _
from odoo.exceptions import UserError

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
        base_url = ICP.get_param('hupun_connector.api_base_url', 'https://erp-open.hupun.com/api')
        
        if not app_key or not app_secret:
            raise UserError(_("Hupun App Key and App Secret must be configured in settings."))
            
        return app_key, app_secret, base_url

    def _generate_signature(self, params, app_secret, is_open_api=True):
        """
        Generates the signature for Hupun API.
        """
        # 1. Sort parameters by key
        sorted_keys = sorted(params.keys())
        
        # 2. Start with secret key
        string_to_be_signed = app_secret
        
        # 3. Concatenate parameters
        for key in sorted_keys:
            val = str(params[key])
            
            if is_open_api:
                # OPEN API: key=encoded_value&
                # Python's quote_plus encodes spaces as +, which matches PHP's urlencode
                encoded_val = urllib.parse.quote_plus(val)
                # PHP SDK specifically replaces %2A with *
                encoded_val = encoded_val.replace('%2A', '*')
                string_to_be_signed += f"{key}={encoded_val}&"
            else:
                # B2C API: keyvalue
                string_to_be_signed += f"{key}{val}"
                
        # For OPEN API, remove trailing '&'
        if is_open_api and string_to_be_signed.endswith('&'):
            string_to_be_signed = string_to_be_signed[:-1]
            
        # 4. Append secret key at the end
        string_to_be_signed += app_secret
        
        # 5. MD5 Hash and Uppercase
        md5_hash = hashlib.md5(string_to_be_signed.encode('utf-8')).hexdigest()
        return md5_hash.upper()

    def make_request(self, endpoint, params=None, method='POST', is_open_api=True):
        """
        Makes a request to the Hupun API.
        :param endpoint: API endpoint (e.g., 'erp/goods/query')
        :param params: Dictionary of business parameters
        :param method: HTTP method (default POST)
        :param is_open_api: True if calling an 'erp/' interface
        :return: JSON response
        """
        app_key, app_secret, base_url = self._get_credentials()
        
        if params is None:
            params = {}
            
        # Add system parameters
        timestamp = str(int(time.time() * 1000))
        
        request_params = params.copy()
        
        if is_open_api:
            request_params.update({
                '_app': app_key,
                '_t': timestamp,
                '_s': '', # Session/Secret usually empty
            })
        else:
            request_params.update({
                'app_key': app_key,
                'timestamp': timestamp,
                'format': 'json',
            })
            
        # Generate signature
        signature = self._generate_signature(request_params, app_secret, is_open_api=is_open_api)
        
        if is_open_api:
            request_params['_sign'] = signature
        else:
            request_params['sign'] = signature
            
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        _logger.info(f"Hupun API Request: {url} Params: {request_params}")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=request_params, timeout=30)
            else:
                # Usually POST requests are form-urlencoded or JSON?
                # The signature construction suggests form-urlencoded for OPEN API usually, 
                # but let's check if we should send as data or json.
                # The PHP SDK usually sends as POST fields.
                response = requests.post(url, data=request_params, timeout=30)
                
            response.raise_for_status()
            result = response.json()
            
            _logger.info(f"Hupun API Response: {result}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            _logger.error(f"Hupun API Request Failed: {e}")
            raise UserError(_("Failed to connect to Hupun API: %s") % str(e))
        except ValueError as e:
            _logger.error(f"Hupun API Invalid JSON: {e}")
            raise UserError(_("Invalid response from Hupun API."))

    # --- Base Info API (基础信息接口) ---
    def shop_query(self, params=None):
        """Query shop information (erp/base/shop/page/get)"""
        return self.make_request('erp/base/shop/page/get', params)

    def supplier_query(self, params=None):
        """Query supplier information (erp/base/supplier/query)"""
        return self.make_request('erp/base/supplier/query', params)

    def supplier_add(self, params):
        """Add supplier (erp/base/supplier/add)"""
        return self.make_request('erp/base/supplier/add', params)

    def supplier_modify(self, params):
        """Modify supplier (erp/base/supplier/modify)"""
        return self.make_request('erp/base/supplier/modify', params)

    def storage_query(self, params=None):
        """Query storage/warehouse information (erp/base/storage/query)"""
        return self.make_request('erp/base/storage/query', params)

    def storage_add(self, params):
        """Add storage/warehouse (erp/base/storage/add)"""
        return self.make_request('erp/base/storage/add', params)

    # --- Inventory API (库存接口) ---
    def inventory_query(self, params=None):
        """Query inventory (erp/stock/query)"""
        return self.make_request('erp/stock/query', params)
        
    def inventory_sync(self, params):
        """Sync inventory quantity (erp/stock/sync)"""
        return self.make_request('erp/stock/sync', params)

    def batch_query_by_bill(self, params):
        """Query batch info by bill code (erp/batch/billbatch)"""
        return self.make_request('erp/batch/billbatch', params)

    # --- Goods API (商品接口) ---
    def goods_query(self, params=None):
        """Query goods information (erp/goods/query)"""
        return self.make_request('erp/goods/query', params)

    def goods_add(self, params):
        """Add new goods (erp/goods/add)"""
        return self.make_request('erp/goods/add', params)

    def goods_update(self, params):
        """Update goods information (erp/goods/update)"""
        return self.make_request('erp/goods/update', params)
        
    def goods_sku_query(self, params=None):
        """Query goods SKU (erp/goods/sku/query)"""
        return self.make_request('erp/goods/sku/query', params)

    def goods_package_add(self, params):
        """Add goods package/bundle (erp/goods/add/goodspackage)"""
        return self.make_request('erp/goods/add/goodspackage', params)

    def goods_category_query(self, params=None):
        """Query goods categories (erp/goods/catagorypage/query/v2)"""
        return self.make_request('erp/goods/catagorypage/query/v2', params)

    # --- Trade API (订单接口) ---
    def trade_query(self, params=None):
        """Query trades/orders (erp/trade/query)"""
        return self.make_request('erp/trade/query', params)

    def trade_add(self, params):
        """Add new trade (erp/trade/add)"""
        return self.make_request('erp/trade/add', params)
        
    def trade_delivery(self, params):
        """Trade delivery/shipping (erp/trade/delivery)"""
        return self.make_request('erp/trade/delivery', params)

    # --- Inventory API (库存接口) ---
    def inventory_query(self, params=None):
        """Query inventory (erp/stock/query)"""
        return self.make_request('erp/stock/query', params)
        
    def inventory_sync(self, params):
        """Sync inventory quantity (erp/stock/sync)"""
        return self.make_request('erp/stock/sync', params)

    # --- Purchase API (采购接口) ---
    def purchase_query(self, params=None):
        """Query purchase orders (erp/purchase/query)"""
        return self.make_request('erp/purchase/query', params)

    def purchase_add(self, params):
        """Add purchase order (erp/purchase/add)"""
        return self.make_request('erp/purchase/add', params)

    def purchase_bill_add(self, params):
        """Add purchase bill (erp/purchase/purchasebill/add)"""
        return self.make_request('erp/purchase/purchasebill/add', params)

    # --- Finance/BI API (财务/BI接口) ---
    def platform_bill_query(self, params=None):
        """Query platform bills (erp/bi/service/bill/platformbill/querybill)"""
        return self.make_request('erp/bi/service/bill/platformbill/querybill', params)

    # --- After Sales API (售后接口) ---
    def refund_query(self, params=None):
        """Query refund/return orders (erp/refund/query)"""
        return self.make_request('erp/refund/query', params)

