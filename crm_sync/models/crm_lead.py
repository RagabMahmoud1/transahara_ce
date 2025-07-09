import requests
import logging
from odoo import models, api,fields
from odoo.tools.safe_eval import datetime

_logger = logging.getLogger(__name__)

class ResUser(models.Model):
    _inherit = 'res.users'
    external_user_id = fields.Integer( string="External User ID", copy=False)
    external_user_name = fields.Char( string="External User Name", copy=False)

    # (constrain for external_user_name,external_user_id unique)
    _sql_constraints = [
        ('external_user_name_unique', 'unique(external_user_name)', 'The external user name must be unique!'),
        ('external_user_id_unique', 'unique(external_user_id)', 'The external user ID must be unique!'),
    ]

class ResPartner(models.Model):
    _inherit = 'res.partner'

    external_id = fields.Integer("External ID", copy=False)
    external_user_id = fields.Integer(string="External User ID", copy=False)
    external_user_name = fields.Char(string="External User Name", copy=False)
    is_external_request = fields.Boolean(string="External Request", )

    def _get_peer_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('crm_sync.peer_url')
        return base_url.replace('crm.lead', 'res.partner')

    @api.model
    def create(self, vals):
        is_auto_sync = self.env['ir.config_parameter'].sudo().get_param('crm_sync.auto_sync')
        if not is_auto_sync:
            vals["is_external_request"] = True
            return super().create(vals)

        if vals.get('is_external_request', False) == False:
            partner = super().create(vals)

            try:
                user = self.env['res.users'].browse(vals.get('user_id', self.env.uid))
                external_user_id = user.external_user_id if user else None
                external_user_name = user.external_user_name if user else None
                vals["is_external_request"] = True
                vals["external_id"] = partner.id
                vals["external_user_id"] = user.id
                payload = vals
                if external_user_id:
                    payload['user_id'] = external_user_id
                peer_url = self._get_peer_url()
                _logger.warning(f"payload: {payload}")
                response = requests.post(peer_url, json=payload)
                _logger.info(f"Sync Response (create): {response.status_code} - {response.text}")
                if response.status_code == 200:
                    response_data = response.json()
                    if 'content' in response_data and 'id' in response_data['content']:
                        partner.write(
                            {
                                'external_id': response_data['content']['id'],
                                'is_external_request': True,
                            }
                        )
            except Exception as e:
                _logger.error(f"Sync Error (create): {e}")

            return partner
        else:
            vals["is_external_request"] = True
            partner1 = super().create(vals)
            return partner1

    def write(self, vals):
        is_auto_sync = self.env['ir.config_parameter'].sudo().get_param('crm_sync.auto_sync')
        if not is_auto_sync:
            vals["is_external_request"] = True
            return super().write(vals)

        if vals.get('is_external_request', False) == False:
            res = super().write(vals)

            for partner in self:
                payload = {}
                for key, value in vals.items():
                    if isinstance(value, datetime.datetime):
                        payload[key] = value.isoformat()
                    else:
                        payload[key] = value
                payload["external_id"] = partner.id
                payload["is_external_request"] = True
                peer_url = f"{self._get_peer_url()}/{partner.external_id}"
                e_partner = requests.post(peer_url, json=payload)
                _logger.info(f"Sync Response (write): {e_partner.status_code} - {e_partner.text}")

            return res
        else:
            vals["is_external_request"] = True
            res1 = super().write(vals)
            return res1

    def unlink(self):
        is_auto_sync = self.env['ir.config_parameter'].sudo().get_param('crm_sync.auto_sync')
        if not is_auto_sync:
            return super().unlink()

        external_ids = self.mapped('external_id')
        if not external_ids:
            return super().unlink()

        res = super().unlink()
        self.env.cr.commit()
        for ext_id in external_ids:
            if not ext_id or ext_id <= 0:
                _logger.warning(f"Skipping unlink for invalid external ID: {ext_id}")
                continue
            peer_url = f"{self._get_peer_url()}/{ext_id}"
            external_partner = requests.get(peer_url)
            if external_partner.status_code != 200:
                _logger.error(f"Failed to fetch partner with external ID {ext_id}: {external_partner.text}")
                continue
            requests.delete(peer_url)
            _logger.info(f"Sync Response (unlink): {external_partner.status_code} - {external_partner.text}")

        return res



class CrmLead(models.Model):
    _inherit = 'crm.lead'
    external_id = fields.Integer("External ID")
    external_user_id = fields.Integer(string="External User ID", )
    external_user_name = fields.Char(string="External User Name", )
    is_external_request = fields.Boolean(string="External Request",)

    def _get_peer_url(self):
        """
        Determine the peer instance API endpoint.
        Adjust this logic based on your deployment environment.
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('crm_sync.peer_url')
        _logger.warning(f"Peer URL from config: {base_url}")
        return base_url or False


    @api.model
    def create(self, vals):
        is_auto_sync = self.env['ir.config_parameter'].sudo().get_param('crm_sync.auto_sync')
        if not is_auto_sync:
            vals["is_external_request"] = True
            return super().create(vals)

        if vals.get('is_external_request', False) == False:
            lead = super().create(vals)

            try:
                user = self.env['res.users'].browse(vals.get('user_id', self.env.uid))
                external_user_id = user.external_user_id if user else None
                external_user_name = user.external_user_name if user else None
                vals["is_external_request"] = True
                vals["external_id"] = lead.id
                vals["external_user_id"] = user.id
                vals["external_user_name"] = external_user_name

                if vals.get('partner_id'):
                    partner = self.env['res.partner'].browse(vals['partner_id'])
                    if partner:
                        if partner.external_id:
                            vals['partner_id'] = partner.external_id
                        else:
                            # If partner does not have an external ID, we can create it
                            partner_vals = {
                                'name': partner.name,
                                'email': partner.email,
                                'phone': partner.phone,
                                'mobile': partner.mobile,
                                'external_user_id': external_user_id,
                                'external_user_name': external_user_name,
                            }
                            new_partner = self.env['res.partner'].create(partner_vals)
                            vals['partner_id'] = new_partner.id
                # Prepare the payload for the external system

                payload = vals
                # update payload with user_id = external_user_id
                if external_user_id:
                    payload['user_id'] = external_user_id
                peer_url = self._get_peer_url()
                _logger.warning(f"payload: {payload}")
                # remove field 'date_open' from vals
                if 'date_open' in payload:
                    del payload['date_open']
                response = requests.post(peer_url, json=payload)
                _logger.info(f"Sync Response (create): {response.status_code} - {response.text}")
                # response.text = '{"content": {"id": 57, "write_date": "06/16/2025 16:52:24", "contact_name": "", "display_name": "Test EE 9", "partner_name": "", "mobile": "", "external_id": 60, "is_external_request": false, "name": "Test EE 9", "phone": ""}, "code": "200"}'
                # get id from the content from response text
                if response.status_code == 200:
                    response_data = response.json()
                    if 'content' in response_data and 'id' in response_data['content']:
                        lead.write(
                            {
                                'external_id': response_data['content']['id'],
                                'is_external_request': True,
                             }

                        )
            except Exception as e:
                _logger.error(f"Sync Error (create): {e}")

            return lead
        else:
            vals["is_external_request"] = True
            lead1 = super().create(vals)
            return lead1

    def write(self, vals):

        is_auto_sync = self.env['ir.config_parameter'].sudo().get_param('crm_sync.auto_sync')
        if not is_auto_sync:
            vals["is_external_request"] = True
            return super().write(vals)

        if vals.get('is_external_request', False) == False:
            res = super().write(vals)

            for lead in self:
                payload = {}
                for key, value in vals.items():
                    if isinstance(value, datetime.datetime):
                        payload[key] = value.isoformat()
                    else:
                        payload[key] = value
                payload["external_id"] = lead.id
                payload["is_external_request"] = True
                peer_url = f"{self._get_peer_url()}/{lead.external_id}"
                if 'date_open' in payload:
                    del payload['date_open']
                e_lead = requests.post(peer_url, json=payload)
                _logger.info(f"Sync Response (write): {e_lead.status_code} - {e_lead.text}")

            return res
        else:
            # If this is an external request, we should not sync back to the peer.
            # Just remove the flag for future writes.
            vals["is_external_request"] = True
            res1 = super().write(vals)

            return res1

    def unlink(self):
        is_auto_sync = self.env['ir.config_parameter'].sudo().get_param('crm_sync.auto_sync')
        if not is_auto_sync:
            return super().unlink()

        external_ids = self.mapped('external_id')
        if not external_ids:
            return super().unlink()

        res = super().unlink()
        self.env.cr.commit()
        for ext_id in external_ids:
            if not ext_id or ext_id <= 0:
                _logger.warning(f"Skipping unlink for invalid external ID: {ext_id}")
                continue
            peer_url = f"{self._get_peer_url()}/{ext_id}"
            external_lead = requests.get(peer_url)
            if external_lead.status_code != 200:
                _logger.error(f"Failed to fetch lead with external ID {ext_id}: {external_lead.text}")
                continue
            requests.delete(peer_url)
            _logger.info(f"Sync Response (unlink): {external_lead.status_code} - {external_lead.text}")

        return res