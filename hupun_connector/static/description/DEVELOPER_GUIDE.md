# Hupun Connector 二次开发指南

## 目录

1. [模块概述](#模块概述)
2. [架构设计](#架构设计)
3. [核心组件说明](#核心组件说明)
4. [快速开始](#快速开始)
5. [API调用方法](#api调用方法)
6. [添加新接口](#添加新接口)
7. [数据同步开发](#数据同步开发)
8. [最佳实践](#最佳实践)
9. [常见问题](#常见问题)

---

## 模块概述

`hupun_connector` 是一个 Odoo 17 模块，用于与万里牛ERP (Hupun) 系统进行数据对接。该模块提供了：

- **统一的 API 客户端**：封装了 Hupun 官方的签名和请求逻辑
- **配置管理**：系统设置中配置 API 凭证
- **同步日志**：记录所有同步操作的状态和详情
- **示例实现**：产品同步、订单同步的完整示例

### 依赖模块

```python
'depends': ['base', 'sale_management', 'stock', 'purchase']
```

---

## 架构设计

```
hupun_connector/
├── models/
│   ├── hupun_api.py          # 核心 API 客户端 (AbstractModel)
│   ├── hupun_request.py      # 官方请求类 (签名/加密/HTTP)
│   ├── hupun_endpoints.py    # API 端点常量
│   ├── hupun_sync_log.py     # 同步日志模型
│   ├── res_config_settings.py # 系统配置
│   ├── product_product.py    # 产品同步示例
│   └── sale_order.py         # 订单同步示例
├── views/
│   ├── hupun_menus.xml       # 菜单定义
│   ├── res_config_settings_views.xml
│   ├── hupun_sync_log_views.xml
│   ├── product_views.xml
│   └── sale_order_views.xml
├── security/
│   ├── hupun_security.xml    # 权限组
│   └── ir.model.access.csv   # 模型访问权限
└── data/
    └── ir_cron_data.xml      # 定时任务
```

### 调用流程

```
业务代码 → hupun.api (AbstractModel) → Request类 → Hupun API
                ↓
         hupun.sync.log (记录日志)
```

---

## 核心组件说明

### 1. HupunAPI (`hupun_api.py`)

这是核心的 API 客户端，作为 `AbstractModel` 实现，可以在任何地方调用。

```python
class HupunAPI(models.AbstractModel):
    _name = 'hupun.api'
    _description = 'Hupun API Client'
```

**主要方法：**

| 方法 | 说明 | 端点 |
|------|------|------|
| `make_request(endpoint, params)` | 通用请求方法 | 任意端点 |
| `shop_query(params)` | 查询店铺 | erp/base/shop/page/get |
| `goods_query(params)` | 查询商品 | erp/goods/spec/open/query/goodswithspeclist |
| `goods_add(params)` | 添加商品 | erp/goods/add/item |
| `trade_query(params)` | 查询订单 | erp/trade/query |
| `order_list_trades(params)` | 查询开放订单 | erp/opentrade/list/trades |
| `inventory_query(params)` | 查询库存 | erp/stock/query |

### 2. Request 类 (`hupun_request.py`)

这是官方提供的请求执行类，负责：
- 参数签名 (MD5/HMAC)
- HTTP POST 请求
- GZIP 压缩
- URL 编码

**无需直接使用此类**，通过 `hupun.api` 调用即可。

### 3. HupunSyncLog (`hupun_sync_log.py`)

同步日志模型，记录每次同步操作。

```python
class HupunSyncLog(models.Model):
    _name = 'hupun.sync.log'
    
    name = fields.Char()
    sync_type = fields.Selection([
        ('product', 'Products'),
        ('order', 'Orders'),
        ('stock', 'Stock'),
        ('other', 'Other'),
    ])
    status = fields.Selection([
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ])
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    summary = fields.Char()
    details = fields.Text()
    request_data = fields.Text()
    response_data = fields.Text()
```

**便捷方法：**
- `mark_success(summary)` - 标记成功
- `mark_failed(error_msg)` - 标记失败

---

## 快速开始

### 1. 获取 API 客户端

```python
# 在任何 Odoo 模型中
client = self.env['hupun.api']
```

### 2. 调用 API

```python
# 查询店铺
result = client.shop_query({
    'page': 1,
    'limit': 10,
})

# 检查结果
if result.get('code') == 0:
    data = result.get('data')
    # 处理数据...
else:
    error_msg = result.get('message')
    # 处理错误...
```

### 3. 使用自定义端点

```python
# 直接调用任意端点
result = client.make_request('erp/your/endpoint', {
    'param1': 'value1',
    'param2': 'value2',
})
```

---

## API调用方法

### 基础调用模式

```python
def my_sync_method(self):
    client = self.env['hupun.api']
    
    try:
        result = client.goods_query({
            'page': 1,
            'limit': 100,
            'item_code': 'SKU001',
        })
        
        if result.get('code') != 0:
            raise UserError(f"API Error: {result.get('message')}")
        
        data = result.get('data', {})
        items = data.get('list', []) if isinstance(data, dict) else data
        
        for item in items:
            # 处理每条记录...
            pass
            
    except Exception as e:
        _logger.error(f"Sync failed: {e}")
        raise
```

### 分页查询

```python
def fetch_all_items(self):
    client = self.env['hupun.api']
    all_items = []
    page = 1
    limit = 100
    
    while True:
        result = client.goods_query({
            'page': page,
            'limit': limit,
        })
        
        if result.get('code') != 0:
            break
            
        data = result.get('data', {})
        items = data.get('list', []) if isinstance(data, dict) else data
        
        if not items:
            break
            
        all_items.extend(items)
        
        # 检查是否还有更多数据
        total = data.get('total', 0) if isinstance(data, dict) else len(items)
        if len(all_items) >= total or len(items) < limit:
            break
            
        page += 1
    
    return all_items
```

---

## 添加新接口

### 步骤 1: 添加端点常量

在 `hupun_endpoints.py` 中添加：

```python
# 新增采购退货接口
PURCHASE_RETURN_QUERY = 'erp/purchase/return/query'
PURCHASE_RETURN_ADD = 'erp/purchase/return/add'
```

### 步骤 2: 添加 API 方法

在 `hupun_api.py` 中添加：

```python
# --- Purchase Return API (采购退货接口) ---
def purchase_return_query(self, params=None):
    """Query purchase returns (erp/purchase/return/query)"""
    return self.make_request(hupun_endpoints.PURCHASE_RETURN_QUERY, params)

def purchase_return_add(self, params):
    """Add purchase return (erp/purchase/return/add)"""
    return self.make_request(hupun_endpoints.PURCHASE_RETURN_ADD, params)
```

### 步骤 3: 使用新接口

```python
client = self.env['hupun.api']
result = client.purchase_return_query({'page': 1, 'limit': 50})
```

---

## 数据同步开发

### 完整的同步方法模板

```python
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class YourModel(models.Model):
    _inherit = 'your.model'
    
    # 添加 Hupun 相关字段
    hupun_id = fields.Char(string='Hupun ID', index=True)
    is_hupun_synced = fields.Boolean(string='Synced to Hupun', default=False)
    hupun_last_sync = fields.Datetime(string='Last Sync Time')
    
    def action_sync_to_hupun(self):
        """手动同步按钮"""
        client = self.env['hupun.api']
        SyncLog = self.env['hupun.sync.log']
        
        # 创建同步日志
        log = SyncLog.create({
            'name': _('Sync %s to Hupun') % self._description,
            'sync_type': 'other',  # 或自定义类型
            'status': 'running',
        })
        
        success_count = 0
        fail_count = 0
        details = []
        
        for record in self:
            try:
                # 准备数据
                params = record._prepare_hupun_data()
                
                # 调用 API
                if record.hupun_id:
                    # 更新
                    result = client.make_request('erp/your/update', params)
                else:
                    # 新增
                    result = client.make_request('erp/your/add', params)
                
                # 检查结果
                if result.get('code') == 0:
                    record.write({
                        'is_hupun_synced': True,
                        'hupun_last_sync': fields.Datetime.now(),
                        'hupun_id': result.get('data', {}).get('id'),
                    })
                    success_count += 1
                    details.append(f"✓ {record.name}")
                else:
                    fail_count += 1
                    details.append(f"✗ {record.name}: {result.get('message')}")
                    
            except Exception as e:
                fail_count += 1
                details.append(f"✗ {record.name}: {str(e)}")
                _logger.error(f"Sync failed for {record.name}: {e}")
        
        # 更新日志
        log.write({
            'details': '\n'.join(details),
        })
        
        if fail_count == 0:
            log.mark_success(f"Synced {success_count} records")
        elif success_count == 0:
            log.mark_failed(f"All {fail_count} records failed")
        else:
            log.write({
                'status': 'partial',
                'end_time': fields.Datetime.now(),
                'summary': f"Success: {success_count}, Failed: {fail_count}",
            })
        
        return self._show_notification(success_count, fail_count)
    
    def _prepare_hupun_data(self):
        """准备发送到 Hupun 的数据"""
        self.ensure_one()
        return {
            'code': self.name,
            # 添加更多字段映射...
        }
    
    def _show_notification(self, success, fail):
        """显示通知"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sync Complete'),
                'message': _('Success: %d, Failed: %d') % (success, fail),
                'type': 'success' if fail == 0 else 'warning',
                'sticky': False,
            }
        }
    
    @api.model
    def cron_sync_to_hupun(self):
        """定时任务同步"""
        records = self.search([
            ('is_hupun_synced', '=', False),
            # 添加其他过滤条件...
        ])
        records.action_sync_to_hupun()
```

### 添加定时任务

在 `data/ir_cron_data.xml` 中添加：

```xml
<record id="ir_cron_sync_your_model" model="ir.cron">
    <field name="name">Hupun: Sync Your Model</field>
    <field name="model_id" ref="your_module.model_your_model"/>
    <field name="state">code</field>
    <field name="code">model.cron_sync_to_hupun()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">hours</field>
    <field name="numbercall">-1</field>
    <field name="active" eval="True"/>
</record>
```

### 添加视图按钮

在视图 XML 中添加同步按钮：

```xml
<record id="your_model_view_form" model="ir.ui.view">
    <field name="name">your.model.form.hupun</field>
    <field name="model">your.model</field>
    <field name="inherit_id" ref="your_module.your_model_view_form"/>
    <field name="arch" type="xml">
        <xpath expr="//header" position="inside">
            <button name="action_sync_to_hupun" 
                    string="Sync to Hupun" 
                    type="object" 
                    class="btn-primary"
                    groups="hupun_connector.group_hupun_user"/>
        </xpath>
        <xpath expr="//sheet" position="inside">
            <group string="Hupun Info">
                <field name="hupun_id" readonly="1"/>
                <field name="is_hupun_synced" readonly="1"/>
                <field name="hupun_last_sync" readonly="1"/>
            </group>
        </xpath>
    </field>
</record>
```

---

## 最佳实践

### 1. 错误处理

```python
from odoo.exceptions import UserError

try:
    result = client.goods_query(params)
except Exception as e:
    _logger.error(f"API request failed: {e}")
    raise UserError(_("Failed to connect to Hupun: %s") % str(e))

# 检查业务错误
if result.get('code') != 0:
    _logger.warning(f"Hupun API returned error: {result}")
    # 根据场景决定是否抛出异常或继续处理
```

### 2. 使用同步日志

```python
def sync_with_logging(self):
    log = self.env['hupun.sync.log'].create({
        'name': 'My Sync Task',
        'sync_type': 'other',
    })
    
    try:
        # 执行同步...
        log.mark_success("Completed successfully")
    except Exception as e:
        log.mark_failed(str(e))
        raise
```

### 3. 批量处理

```python
# 使用批量处理减少 API 调用
BATCH_SIZE = 50

for i in range(0, len(records), BATCH_SIZE):
    batch = records[i:i + BATCH_SIZE]
    
    # 收集批量数据
    batch_data = []
    for record in batch:
        batch_data.append(record._prepare_hupun_data())
    
    # 如果 API 支持批量操作
    result = client.make_request('erp/batch/endpoint', {'items': batch_data})
    
    # 提交事务避免长时间锁定
    self.env.cr.commit()
```

### 4. 字段映射

```python
# 建议创建映射配置
HUPUN_FIELD_MAP = {
    'item_code': 'default_code',
    'item_name': 'name',
    'bar_code': 'barcode',
    'sale_price': 'list_price',
}

def _map_hupun_to_odoo(self, hupun_data):
    """将 Hupun 数据映射到 Odoo 字段"""
    odoo_vals = {}
    for hupun_field, odoo_field in HUPUN_FIELD_MAP.items():
        if hupun_field in hupun_data:
            odoo_vals[odoo_field] = hupun_data[hupun_field]
    return odoo_vals
```

### 5. 权限控制

在 `security/ir.model.access.csv` 中添加权限：

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_your_model_user,your.model user,model_your_model,hupun_connector.group_hupun_user,1,0,0,0
access_your_model_manager,your.model manager,model_your_model,hupun_connector.group_hupun_manager,1,1,1,1
```

---

## 常见问题

### Q1: 如何测试 API 连接？

进入 **Hupun > Configuration > Settings**，填写 API 凭证后点击 **Test Connection** 按钮。

### Q2: API 返回签名错误？

检查以下几点：
1. `App Key` 和 `App Secret` 是否正确
2. 服务器时间是否正确（签名包含时间戳）
3. `API Base URL` 格式是否正确（应为 `https://open-api.hupun.com/api`）

### Q3: 如何查看请求/响应详情？

1. 查看同步日志：**Hupun > Configuration > Sync Logs**
2. 查看 Odoo 日志：过滤 `hupun` 或 `open.hopen` 关键字

### Q4: 如何处理大量数据同步？

1. 使用分页查询
2. 使用定时任务（Cron）
3. 实现增量同步（基于时间戳或状态）
4. 批量提交事务

### Q5: 如何扩展 sync_type？

在 `hupun_sync_log.py` 中修改 `sync_type` 字段的 Selection：

```python
sync_type = fields.Selection([
    ('product', 'Products'),
    ('order', 'Orders'),
    ('stock', 'Stock'),
    ('purchase', 'Purchase'),  # 新增
    ('refund', 'Refund'),      # 新增
    ('other', 'Other'),
], string='Sync Type', required=True, default='other')
```

---

## 附录：已实现的 API 列表

### 基础信息接口

| 方法 | 端点 | 说明 |
|------|------|------|
| `shop_query` | erp/base/shop/page/get | 查询店铺 |
| `supplier_query` | erp/base/supplier/query | 查询供应商 |
| `supplier_add` | erp/base/supplier/add | 添加供应商 |
| `storage_query` | erp/base/storage/query | 查询仓库 |

### 商品接口

| 方法 | 端点 | 说明 |
|------|------|------|
| `goods_query` | erp/goods/spec/open/query/goodswithspeclist | 查询商品 |
| `goods_add` | erp/goods/add/item | 添加商品 |
| `goods_update` | erp/goods/update/item | 更新商品 |
| `goods_sku_query` | erp/goods/sku/query | 查询SKU |
| `goods_category_query` | erp/goods/catagorypage/query/v2 | 查询分类 |

### 订单接口

| 方法 | 端点 | 说明 |
|------|------|------|
| `trade_query` | erp/trade/query | 查询订单 |
| `order_list_trades` | erp/opentrade/list/trades | 查询开放订单 |
| `order_trade_commit` | erp/opentrade/trade/commit | 提交订单 |
| `order_modify_address` | erp/opentrade/modify/address | 修改地址 |

### 库存接口

| 方法 | 端点 | 说明 |
|------|------|------|
| `inventory_query` | erp/stock/query | 查询库存 |
| `inventory_sync` | erp/stock/sync | 同步库存 |

### 采购接口

| 方法 | 端点 | 说明 |
|------|------|------|
| `purchase_query` | erp/purchase/query | 查询采购单 |
| `purchase_add` | erp/purchase/add | 添加采购单 |

---

## 版本历史

- **v1.0** - 初始版本，包含基础框架和产品/订单同步示例
