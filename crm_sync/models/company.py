from odoo import api, fields, models

class Company(models.Model):
    _inherit = 'res.company'

    is_auto_sync = fields.Boolean(string='Auto Sync', default=False)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_auto_sync = fields.Boolean(related='company_id.is_auto_sync', string='Auto Sync', readonly=False, config_parameter="crm_sync.auto_sync")