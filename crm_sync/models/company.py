from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_auto_sync = fields.Boolean(string='Auto Sync', readonly=False, config_parameter="crm_sync.auto_sync")