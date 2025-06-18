import requests
import logging
from odoo import models, api,fields
from odoo.tools.safe_eval import datetime

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    external_id = fields.Integer("External ID")

    is_external_request = fields.Boolean(string="External Request",)

    def _get_peer_url(self):
        """
        Determine the peer instance API endpoint.
        Adjust this logic based on your deployment environment.
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('crm_sync.peer_url')
        return base_url or 'http://localhost:8069/kw_api/custom/crm.lead'  # fallback


    @api.model
    def create(self, vals):
        if vals.get('is_external_request', False) == False:
            lead = super().create(vals)

            try:
                vals["is_external_request"] = True
                vals["external_id"] = lead.id
                payload = vals
                peer_url = self._get_peer_url()
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
            vals["is_external_request"]= False
            lead1 = super().create(vals)
            return lead1

    def write(self, vals):

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
            vals["is_external_request"] = False
            res1 = super().write(vals)

            return res1

    def unlink(self):
        external_ids = self.mapped('external_id')
        if not external_ids:
            return super().unlink()

        res = super().unlink()
        self.env.cr.commit()
        for ext_id in external_ids:
            peer_url = f"{self._get_peer_url()}/{ext_id}"
            external_lead = requests.get(peer_url)
            if external_lead.status_code != 200:
                _logger.error(f"Failed to fetch lead with external ID {ext_id}: {external_lead.text}")
                continue
            requests.delete(peer_url)
            _logger.info(f"Sync Response (unlink): {external_lead.status_code} - {external_lead.text}")

        return res