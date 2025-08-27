# from . import crm_lead
# from . import mail_activity
# from . import model_extensions
from . import company
from . import sync_mixin
# from . import sync_models

from odoo import models, fields

EXTS = [
    ('crm.lead', 'External Lead Ref'),
    ('res.partner', 'External Partner Ref'),
    ('crm.team', 'External Team Ref'),
    ('crm.team.member', 'External Team Member Ref'),
    ('crm.stage', 'External Stage Ref'),
    ('utm.source', 'External UTM Source Ref'),
    ('utm.campaign', 'External UTM Campaign Ref'),
    ('utm.medium', 'External UTM Medium Ref'),
    ('crm.tag', 'External Tag Ref'),
    ('res.country', 'External Country Ref'),
    ('res.country.state', 'External State Ref'),
    ('res.partner.industry', 'External Industry Ref'),
    ('mail.activity', 'External Activity Ref'),
    ('mail.activity.type', 'External Activity Type Ref'),
    ('mail.message', 'External Message Ref'),
    ('crm.lost.reason', 'External Lost Reason Ref'),
    ('res.partner.category', 'External Partner Category Ref'),
    ('res.partner.title', 'External Partner Title Ref'),
]


def extend_sync_models():
    for model_name, label in EXTS:
        type(
            f"{model_name.replace('.', '_').title()}SyncInherit",
            (models.Model,),
            {
                "_inherit": [model_name, "sync.mixin"],
                "_name": model_name,  # keep original
                "__module__": __name__,
                # Optionally override field label
                "external_ref": fields.Integer("External Reference", copy=False, index=True),
                "external_id": fields.Integer("External ID", help="ID of the activity in the external system"),
                "external_employee_id2": fields.Integer("External Employee"),
                "external_employee_name": fields.Char(string="External Employee Name", copy=False),
                "external_user_id": fields.Integer(string="External User ID", copy=False),
                "external_user_name": fields.Char(string="External User Name", copy=False),
                "external_user_password": fields.Char(string="External User Password", copy=False),
                "is_external_request": fields.Boolean(string="External Request"),
                "is_external_request_create": fields.Boolean(string="External Request create"),
                "is_external_request_write": fields.Boolean(string="External Request write"),
                "is_external_request_unlink": fields.Boolean(string="External Request unlink"),
            }
        )


extend_sync_models()
