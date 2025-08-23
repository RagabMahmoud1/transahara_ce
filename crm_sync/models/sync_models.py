from odoo import models, fields
from .sync_mixin import SyncMixin

MODELS_TO_SYNC = [
    "crm.lead",
    "res.partner",
    "res.users",
    "crm.team",
    "crm.stage",
    "crm.tag",
    "utm.campaign",
    "utm.medium",
    "utm.source",
    "res.country",
    "res.partner.industry",
    "mail.activity",
    "mail.message",
    "crm.lost.reason",
]
def make_sync_model(model_name):
    class_name = "Sync_%s" % model_name.replace(".", "_")
    return type(class_name, (models.Model,), {
        "_inherit": model_name,
        "_name": model_name,
        "_sync_model": True,
        "_description": "Sync Enabled %s" % model_name,
        # methods
        "create": create,
        "write": write,
        "unlink": unlink,
    })

def create(self, vals):
    record = super(type(self), self).create(vals)
    if not record._sync_should_skip():
        result = record._sync_call_remote("POST", self._name, vals)
        if result and "id" in result:
            record.external_ref = result["id"]
    return record


def write(self, vals):
    res = super(type(self), self).write(vals)
    if not self._sync_should_skip():
        for rec in self:
            if rec.external_ref:
                rec._sync_call_remote("PUT", self._name, vals, record_id=rec.external_ref)
    return res


def unlink(self):
    ids = [rec.external_ref for rec in self if rec.external_ref]
    res = super(type(self), self).unlink()
    if not self._sync_should_skip():
        for ref in ids:
            self._sync_call_remote("DELETE", self._name, record_id=ref)
    return res


# Dynamically register classes
for m in MODELS_TO_SYNC:
    globals()[m.replace(".", "_")] = make_sync_model(m)
