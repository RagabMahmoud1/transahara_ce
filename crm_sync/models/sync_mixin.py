# models/sync_mixin.py
import requests
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    external_employee_id2 = fields.Integer("External Employee ID")
    external_employee_name = fields.Char("External Employee Name", copy=False)
    external_user_id = fields.Integer("External User ID", copy=False)
    external_user_password = fields.Char("External User Password", copy=False)
    external_ref = fields.Integer("External Reference", related='external_user_id', copy=False, index=True)
    external_id = fields.Integer("External ID", related='external_user_id')
    external_user_name = fields.Char("External User Name", copy=False)
    external_user_login = fields.Char("External Login")
    external_token = fields.Char()
    is_external_request = fields.Boolean("External Request")
    is_external_request_create = fields.Boolean("External Request create")
    is_external_request_write = fields.Boolean("External Request write")
    is_external_request_unlink = fields.Boolean("External Request unlink")


class SyncMixin(models.AbstractModel):
    _name = "sync.mixin"
    _description = "Remote Sync Mixin"

    external_ref = fields.Integer("External Reference", copy=False, index=True)
    external_id = fields.Integer("External ID")
    external_employee_id2 = fields.Integer("External Employee ID")
    external_employee_name = fields.Char("External Employee Name", copy=False)
    external_user_id = fields.Integer("External User ID", copy=False)
    external_user_password = fields.Char("External User Password", copy=False)
    external_user_name = fields.Char("External User Name", copy=False)
    external_user_login = fields.Char("External Login")
    external_token = fields.Char()
    is_external_request = fields.Boolean("External Request")
    is_external_request_create = fields.Boolean("External Request create")
    is_external_request_write = fields.Boolean("External Request write")
    is_external_request_unlink = fields.Boolean("External Request unlink")

    # -------------------------------
    # Token helpers
    # -------------------------------
    def _get_token(self):
        """Ensure we have a valid token, else login again."""
        self.ensure_one()
        if self.external_token:
            return self.external_token

        # No token or invalid -> re-login
        return self._login_external_user()

    def _login_external_user(self):
        """Login to remote and store a new token."""
        cfg = self._get_sync_config()
        if not cfg["enabled"]:
            return None
        user = self.env.user
        login = user.external_user_login
        password = user.external_user_password
        if not login or not password:
            _logger.error("No external credentials set for %s", self)
            return None

        url = f"{cfg['base_url'].rstrip('/')}/kw_api/auth/token"
        try:
            res = requests.post(url, json={
                "login": login,
                "password": password,
                "db": cfg["db"],
            }, headers={
                "Content-Type": "application/json",
                "db": cfg["db"],
            })
            if res.status_code in (200, 201):
                data = res.json()
                token = data.get("name") or data.get("refresh_token")
                if token:
                    self.write({"external_token": token})
                    user.external_token = token
                    return token
        except Exception as e:
            _logger.error("External login failed for %s: %s", self, e)

        return None

    # --- Config + Utils ---
    def _sync_should_skip(self):
        return self.env.context.get("from_remote_sync")

    def _get_sync_config(self):
        params = self.env['ir.config_parameter'].sudo()
        return {
            "enabled": params.get_param("db_sync.enabled", "False") == "True",
            "base_url": params.get_param("db_sync.remote_base_url"),
            "db": params.get_param("db_sync.remote_db"),
            "api_key": params.get_param("db_sync.remote_api_key"),
        }

    def _sync_headers(self):
        cfg = self._get_sync_config()
        return {
            "Content-Type": "application/json",
            "db": cfg["db"],
            "login": self.env.user.external_user_login or "",
            "api-key": cfg["api_key"] or "",
        }

    def _sync_related_field_mapping(self, field_name):
        """ Map local record ID to external_ref for related fields """
        field = self._fields.get(field_name)
        model = self.env[field.comodel_name]
        record = model.browse(self[field_name].id)

        if record and hasattr(record, "external_ref"):
            if record and record.external_ref:
                return record.external_ref
            else:
                # sync it first to remote
                return self._sync_related_field(record)
        return False

    def _sync_related_field(self, record):
        if record and record.id:
            _rec_name_field = record._rec_name
            dynamic_payload = {
                "id": record.id,
                "external_ref": record.external_ref,
                _rec_name_field: record[_rec_name_field]
            }
            result = record._sync_call_remote("POST", record._name, dynamic_payload)
            if result and "content" in result and "id" in result["content"]:
                record.with_context(from_remote_sync=True).write({
                    "external_ref": result["content"]["id"],
                    "external_id": result["content"]["id"],
                })
                return result["content"]["id"]
            else:
                return None
        else:
            return None

    def _prepare_payload_with_related_fields(self, payload):
        """ Prepare payload by mapping related fields to their external references """
        if not payload:
            return payload

        new_payload = payload.copy()

        for field_name in payload.keys():
            # check if field is a related field to another model
            if field_name in self._fields and self._fields[field_name].type == "many2one":
                new_id = self._sync_related_field_mapping(field_name)
                if new_id:
                    new_payload[field_name] = new_id
            # Many2Many
            elif field_name in self._fields and self._fields[field_name].type == "many2many":
                related_ids = payload[field_name]
                if isinstance(related_ids, list):
                    new_related_ids = []
                    for rid in related_ids[0][2]:
                        if isinstance(rid, int):
                            related_record = self.env[self._fields[field_name].comodel_name].browse(rid)
                            """        
                            if record and hasattr(record, "external_ref"):
                                if record and record.external_ref:
                                    return record.external_ref"""
                            if related_record and related_record.external_ref:
                                new_related_ids.append(related_record.external_ref)
                            else:
                                new_related_ids.append(self._sync_related_field(related_record))


                    new_payload[field_name] = [(6, 0, new_related_ids)]
        return new_payload

    def _sync_call_remote(self, method, model, payload=None, record_id=None):
        cfg = self._get_sync_config()

        if not cfg["enabled"] or not cfg["base_url"]:
            return None

        url = f"{cfg['base_url'].rstrip('/')}/kw_api/custom/{model}"
        if record_id:
            url += f"/{record_id}"

        # Always ensure valid token
        token = self[0]._get_token()
        headers = self[0]._sync_headers()
        if not token:
            token = self[0]._login_external_user()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            if method == "GET":
                res = requests.get(url, headers=headers, json=payload or {})
            elif method == "POST":
                new_payload = self._prepare_payload_with_related_fields(payload)
                res = requests.post(url, headers=headers, json=new_payload or {})
            elif method == "PUT":
                # check fields that related to other models (dynamic)

                new_payload = self._prepare_payload_with_related_fields(payload)

                res = requests.post(url, headers=headers, json=new_payload or {})
            elif method == "DELETE":
                res = requests.delete(url, headers=headers)
            else:
                return None

            # If unauthorized → try re-login once
            if res.status_code == 401 or res.status_code == 403:
                new_token = self._login_external_user()
                if new_token:
                    headers["Authorization"] = f"Bearer {new_token}"
                    # retry once
                    if method == "GET":
                        res = requests.get(url, headers=headers, json=payload or {})
                    elif method == "POST":
                        res = requests.post(url, headers=headers, json=payload or {})
                    elif method == "PUT":
                        res = requests.post(url, headers=headers, json=payload or {})
                    elif method == "DELETE":
                        res = requests.delete(url, headers=headers)

            if res.status_code in (200, 201):
                return res.json()

        except Exception as e:
            self.env["ir.logging"].create({
                "name": "DB Sync Bridge",
                "type": "server",
                "dbname": self.env.cr.dbname,
                "level": "ERROR",
                "message": str(e),
                "path": __name__,
                "func": "_sync_call_remote",
                "line": "0",
            })
        return None

    # --- CRUD Hooks ---
    @api.model_create_single
    def create(self, vals):
        record = super(SyncMixin, self).create(vals)
        if not record._sync_should_skip():
            vals["external_id"] = record.id
            vals["external_employee_id2"] = record.env.user.employee_ids[
                                            :1].id if record.env.user.employee_ids else None
            vals["external_employee_name"] = record.env.user.employee_ids[
                                             :1].name if record.env.user.employee_ids else None
            vals["external_ref"] = record.id  # Ensure no external_ref is sent on create
            vals["external_user_id"] = record.env.user.id
            vals["external_user_name"] = record.env.user.name

            result = record._sync_call_remote("POST", self._name, vals)
            if result and "content" in result and "id" in result["content"]:
                # record.external_ref = result["id"]
                record.with_context(from_remote_sync=True).write({
                    "external_ref": result["content"]["id"],
                    "external_id": result["content"]["id"],
                    "external_employee_id2": vals["external_employee_id2"],
                    "external_employee_name": vals["external_employee_name"],
                })
        return record

    def write(self, vals):
        res = super(SyncMixin, self).write(vals)
        if not self._sync_should_skip():
            for rec in self:
                if rec.external_ref:
                    vals["external_id"] = rec.id
                    vals["external_ref"] = rec.id

                    rec._sync_call_remote("PUT", self._name, vals, record_id=rec.external_ref)
        return res

    def unlink(self):
        ids = [rec.external_ref for rec in self if rec.external_ref]
        res = super(SyncMixin, self).unlink()
        if not self._sync_should_skip():
            for ref in ids:
                self._sync_call_remote("DELETE", self._name, record_id=ref)
        return res
