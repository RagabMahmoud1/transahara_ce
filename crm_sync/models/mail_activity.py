import requests
import logging
from odoo import models, api, fields
from odoo.tools.safe_eval import datetime

_logger = logging.getLogger(__name__)
from datetime import date, datetime

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    external_id = fields.Integer("External ID", help="ID of the activity in the external system")
    is_external_request = fields.Boolean(string="External Request",
                                         help="Indicates if this activity was created from an external request")
    external_user_id = fields.Integer(string="External User ID")
    external_user_name = fields.Char(string="External User Name")
    is_external_request_create = fields.Boolean(string="External Request create", )
    is_external_request_write = fields.Boolean(string="External Request write", )
    is_external_request_unlink = fields.Boolean(string="External Request unlink", )

    def _get_peer_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('crm_sync.peer_url')
        return base_url.replace('crm.lead', 'mail.activity')

    @api.model
    def create(self, vals):
        if vals.get('is_external_request_create', False) == False:
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
                vals["is_external_request_create"] = True
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
                            'is_external_request_create': True,
                        })
            except Exception as e:
                _logger.error(f"Sync Error (create): {e}")
            return activity
        else:
            vals["is_external_request_create"] = False

            lead_id = self.env['crm.lead'].browse(vals.get('res_id', False))
            vals['res_model_id'] = self.env['ir.model']._get('crm.lead').id if lead_id else False
            ac = super().create(vals)
            return ac

    def write(self, vals):
        is_auto_sync = self.env['ir.config_parameter'].sudo().get_param('crm_sync.auto_sync')

        if not is_auto_sync:
            vals["is_external_request_write"] = True
            return super().write(vals)

        if vals.get('is_external_request_write', False) is False and not vals.get('is_external_request_create', False):
            res = super().write(vals)

            for record in self:
                try:
                    external_id = record.external_id
                    if not external_id:
                        _logger.warning(f"Skipping sync for record ID {record.id} (no external_id).")
                        continue

                    raw_payload = record.read()[0]
                    payload = {}

                    for key, value in raw_payload.items():
                        if isinstance(value, (datetime, date)):
                            payload[key] = value.isoformat()
                        elif isinstance(value, tuple) and len(value) == 2:
                            payload[key] = value[0]  # Just send the ID
                        else:
                            payload[key] = value

                    vals["is_external_request_write"] = True

                    peer_url = f"{record._get_peer_url()}/{external_id}"
                    response = requests.post(peer_url, json=vals)

                    _logger.info(f"Sync Response (write): {response.status_code} - {response.text}")

                    if response.status_code == 200:
                        response_data = response.json()
                        content = response_data.get('content', {})
                        if 'id' in content:
                            record.write({
                                'external_id': content['id'],
                                'is_external_request_write': True,
                            })

                except Exception as e:
                    _logger.error(f"Sync Error (write) for record {record.id}: {e}")

            return res
        else:
            vals["is_external_request_write"] = False
            return super().write(vals)


    def unlink(self):
        self = self.sudo()
        for activity in self:
            if not activity.external_id or activity.external_id <= 0:
                _logger.warning(f"Skipping unlink for activity {activity.id} with invalid external ID.")
                continue

            is_auto_sync = self.env['ir.config_parameter'].sudo().get_param('crm_sync.auto_sync')
            if not is_auto_sync:
                return super().unlink()

            peer_url = f"{activity._get_peer_url()}/{activity.external_id}"
            try:
                response = requests.delete(peer_url)
                response_text = response.text if response.text else "No content"
                _logger.info(f"Sync Response (unlink): {response.status_code} - {response_text}")
            except Exception as e:
                _logger.error(f"Sync Error (unlink) for activity {activity.id}: {e}")

        res = super(MailActivity, self).unlink()
        return res

class MailMessage(models.Model):
    _inherit = 'mail.message'

    external_id = fields.Integer("External ID", help="ID of the message in the external system")
    is_external_request = fields.Boolean(string="External Request",
                                         help="Indicates if this message was created from an external request")
    external_user_id = fields.Integer(string="External User ID")
    external_user_name = fields.Char(string="External User Name")
    is_external_request_create = fields.Boolean(string="External Request create", )
    is_external_request_write = fields.Boolean(string="External Request write", )
    is_external_request_unlink = fields.Boolean(string="External Request unlink", )

    def _get_peer_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('crm_sync.peer_url')
        return base_url.replace('crm.lead', 'mail.message')

    @api.model
    def create(self, vals):
        if vals.get('is_external_request_create', False) == False:
            message = super().create(vals)
            user = self.env.user
            external_user_id = user.external_user_id if user else None
            external_user_name = user.external_user_name if user else None
            if message.model == 'crm.lead':
                lead_id = self.env['crm.lead'].browse(message.res_id)
                if lead_id and lead_id.external_id:
                    external_id = lead_id.external_id
                    vals['res_id'] = external_id
            try:
                vals["is_external_request_create"] = True
                vals["external_id"] = message.id
                vals["external_user_id"] = external_user_id
                vals["external_user_name"] = external_user_name

                payload = vals
                peer_url = self._get_peer_url()
                response = requests.post(peer_url, json=payload)
                if response.status_code == 200:
                    response_data = response.json()
                    if 'content' in response_data and 'id' in response_data['content']:
                        message.write({
                            'external_id': response_data['content']['id'],
                            'is_external_request_create': True,
                        })
            except Exception as e:
                _logger.error(f"Sync Error (create): {e}")
            return message
        else:

            vals["is_external_request_create"] = False
            return super().create(vals)


    def write(self, vals):
        is_auto_sync = self.env['ir.config_parameter'].sudo().get_param('crm_sync.auto_sync')

        if not is_auto_sync:
            vals["is_external_request_write"] = True
            return super().write(vals)

        if vals.get('is_external_request_write', False) is False and not vals.get('is_external_request_create', False):
            res = super().write(vals)

            for record in self:
                try:
                    external_id = record.external_id
                    if not external_id:
                        _logger.warning(f"Skipping sync for record ID {record.id} (no external_id).")
                        continue

                    raw_payload = record.read()[0]
                    payload = {}

                    for key, value in raw_payload.items():
                        if isinstance(value, (datetime, date)):
                            payload[key] = value.isoformat()
                        elif isinstance(value, tuple) and len(value) == 2:
                            payload[key] = value[0]  # Just send the ID
                        else:
                            payload[key] = value

                    vals["is_external_request_write"] = True

                    peer_url = f"{record._get_peer_url()}/{external_id}"
                    response = requests.post(peer_url, json=vals)

                    _logger.info(f"Sync Response (write): {response.status_code} - {response.text}")

                    if response.status_code == 200:
                        response_data = response.json()
                        content = response_data.get('content', {})
                        if 'id' in content:
                            record.write({
                                'external_id': content['id'],
                                'is_external_request_write': True,
                            })

                except Exception as e:
                    _logger.error(f"Sync Error (write) for record {record.id}: {e}")

            return res
        else:
            vals["is_external_request_write"] = False
            return super().write(vals)


    def unlink(self):
        self = self.sudo()
        for message in self:
            if not message.external_id or message.external_id <= 0:
                _logger.warning(f"Skipping unlink for message {message.id} with invalid external ID.")
                continue

            is_auto_sync = self.env['ir.config_parameter'].sudo().get_param('crm_sync.auto_sync')
            if not is_auto_sync:
                return super().unlink()

            peer_url = f"{message._get_peer_url()}/{message.external_id}"
            try:
                response = requests.delete(peer_url)
                response_text = response.text if response.text else "No content"
                _logger.info(f"Sync Response (unlink): {response.status_code} - {response_text}")
            except Exception as e:
                _logger.error(f"Sync Error (unlink) for message {message.id}: {e}")

        res = super(MailMessage, self).unlink()
        return res
