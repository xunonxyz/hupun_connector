# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HupunSyncLog(models.Model):
    _name = 'hupun.sync.log'
    _description = 'Hupun Synchronization Log'
    _order = 'create_date desc'

    name = fields.Char(string='Name', required=True, default='Sync Log')
    sync_type = fields.Selection([
        ('product', 'Products'),
        ('order', 'Orders'),
        ('stock', 'Stock'),
        ('other', 'Other'),
    ], string='Sync Type', required=True, default='other')
    
    start_time = fields.Datetime(string='Start Time', default=fields.Datetime.now)
    end_time = fields.Datetime(string='End Time')
    status = fields.Selection([
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ], string='Status', default='running')
    
    summary = fields.Char(string='Summary')
    details = fields.Text(string='Details')
    
    request_data = fields.Text(string='Request Data')
    response_data = fields.Text(string='Response Data')

    def mark_success(self, summary="Synchronization successful"):
        self.write({
            'status': 'success',
            'end_time': fields.Datetime.now(),
            'summary': summary
        })

    def mark_failed(self, error_msg):
        self.write({
            'status': 'failed',
            'end_time': fields.Datetime.now(),
            'summary': error_msg
        })
