from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HupunMixin(models.AbstractModel):
    """
    Mixin to integrate with Hupun ERP system.
    """
    _name = 'hupun.mixin'
    _description = 'Hupun Integration Mixin'

    hupun_id = fields.Char(string='Hupun ID', copy=False, index=True, help="Unique ID in Hupun ERP")
    hupun_status = fields.Char(string='Hupun Status', readonly=True)

    def action_sync_hupun_status(self):
        """
        Action to sync status from Hupun.
        """
        self.ensure_one()
        if not self.hupun_id:
            raise UserError(_("No Hupun ID linked to this record."))

        data = self._get_hupun_data()
        if not data:
             raise UserError(_("Record not found in Hupun."))
             
        self._process_hupun_data(data)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync Successful',
                'message': f"Status updated: {self.hupun_status}",
                'type': 'success',
                'sticky': False,
            }
        }

    def _get_hupun_data(self):
        """
        Retrieve data from Hupun API.
        Must be implemented by the inheriting model.
        :return: dict or None
        """
        raise NotImplementedError(_("Method _get_hupun_data must be implemented."))

    def _process_hupun_data(self, data):
        """
        Process the data retrieved from Hupun.
        Can be overridden to handle specific fields.
        """
        self.hupun_status = data.get('status_name') or data.get('status')
