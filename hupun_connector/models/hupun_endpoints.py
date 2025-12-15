# -*- coding: utf-8 -*-

# Base Info API (基础信息接口)
SHOP_QUERY = 'erp/base/shop/page/get'
SUPPLIER_QUERY = 'erp/base/supplier/query'
SUPPLIER_ADD = 'erp/base/supplier/add'
SUPPLIER_MODIFY = 'erp/base/supplier/modify'
STORAGE_QUERY = 'erp/base/storage/query'
STORAGE_ADD = 'erp/base/storage/add'

# Inventory API (库存接口)
INVENTORY_QUERY = 'erp/stock/query'
INVENTORY_SYNC = 'erp/stock/sync'
BATCH_QUERY_BY_BILL = 'erp/batch/billbatch'

# Goods API (商品接口)
GOODS_QUERY = '/erp/goods/spec/open/query/goodswithspeclist'
GOODS_ADD = 'erp/goods/add'
GOODS_UPDATE = 'erp/goods/update'
GOODS_SKU_QUERY = 'erp/goods/sku/query'
GOODS_PACKAGE_ADD = 'erp/goods/add/goodspackage'
GOODS_CATEGORY_QUERY = 'erp/goods/catagorypage/query/v2'

# Trade API (订单接口)
TRADE_QUERY = 'erp/trade/query'
TRADE_OPEN_QUERY = 'erp/opentrade/list/trades'
TRADE_ADD = 'erp/trade/add'
TRADE_DELIVERY = 'erp/trade/delivery'

# Purchase API (采购接口)
PURCHASE_QUERY = 'erp/purchase/query'
PURCHASE_ADD = 'erp/purchase/add'
PURCHASE_BILL_ADD = 'erp/purchase/purchasebill/add'

# Finance/BI API (财务/BI接口)
PLATFORM_BILL_QUERY = 'erp/bi/service/bill/platformbill/querybill'

# After Sales API (售后接口)
REFUND_QUERY = 'erp/refund/query'

# 仓库
WAREHOUSE_QUERY = 'erp/base/storage/query'
