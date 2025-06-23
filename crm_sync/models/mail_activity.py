import requests
import logging
from odoo import models, api,fields
from odoo.tools.safe_eval import datetime

_logger = logging.getLogger(__name__)

# class PortalWizardUser(models.TransientModel):
#     """
#         A model to configure users in the portal wizard.
#     """
#
#     _inherit = 'portal.wizard.user'
#
#     message_subscription = fields.Boolean(
#         string="Message Subscription",
#         help="Subscribe to messages for this user in the portal.",
#         default=True,
#     )


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    external_id = fields.Integer("External ID", help="ID of the activity in the external system")
    is_external_request = fields.Boolean(string="External Request", help="Indicates if this activity was created from an external request")
    external_user_id = fields.Integer(string="External User ID")
    external_user_name = fields.Char(string="External User Name")

    def _get_peer_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('crm_sync.peer_url')
        return base_url.replace('crm.lead', 'mail.activity')

    @api.model
    def create(self, vals):
        if vals.get('is_external_request', False) == False:
            activity = super().create(vals)
            user = self.env.user
            external_user_id = user.external_user_id if user else None
            external_user_name = user.external_user_name if user else None

            if activity.res_model == 'crm.lead':
                lead_id = self.env['crm.lead'].browse(activity.res_id)
                if lead_id and lead_id.external_id:
                    external_id = lead_id.external_id
                    vals['res_id'] = external_id
            try:
                vals["is_external_request"] = True
                vals["external_id"] = activity.id
                vals["external_user_id"] = external_user_id
                vals["external_user_name"] = external_user_name

                payload = vals
                peer_url = self._get_peer_url()
                response = requests.post(peer_url, json=payload)
                if response.status_code == 200:
                    response_data = response.json()
                    if 'content' in response_data and 'id' in response_data['content']:
                        activity.write({
                            'external_id': response_data['content']['id'],
                            'is_external_request': True,
                        })
            except Exception as e:
                _logger.error(f"Sync Error (create): {e}")
            return activity
        else:
            vals["is_external_request"] = False
            user = vals.get('user_id', 0)
            ex_user = vals.get('external_user_id', 0)
            if ex_user and ex_user != 0:
                us = self.env['res.users'].browse(ex_user)
                vals['create_uid'] = us

            if user and user != 0:
                uus = self.env['res.users'].browse(user)
                vals['user_id'] = uus

            lead_id = self.env['crm.lead'].browse(vals.get('res_id', False))
            vals['res_model_id'] = self.env['ir.model']._get('crm.lead').id if lead_id else False
            ac = super().create(vals)
            return ac

    def write(self, vals):
        if vals.get('is_external_request', False) == False:
            res = super().write(vals)

            try:
                vals["is_external_request"] = True
                payload = self.read()[0]
                peer_url = self._get_peer_url()
                response = requests.put(peer_url, json=payload)
                if response.status_code == 200:
                    response_data = response.json()
                    if 'content' in response_data and 'id' in response_data['content']:
                        self.write({
                            'external_id': response_data['content']['id'],
                            'is_external_request': True,
                        })
            except Exception as e:
                _logger.error(f"Sync Error (write): {e}")
            return res
        else:
            vals["is_external_request"] = False
            return super().write(vals)


    def unlink(self):
        if not self.env.context.get('sync_skip'):
            try:
                peer_url = self._get_peer_url()
                for activity in self:
                    response = requests.delete(f"{peer_url}/{activity.external_id}")
                    if response.status_code != 200:
                        _logger.error(f"Sync Error (unlink): {response.status_code} - {response.text}")
            except Exception as e:
                _logger.error(f"Sync Error (unlink): {e}")
        return super().unlink()