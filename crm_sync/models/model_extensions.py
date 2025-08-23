# -*- coding: utf-8 -*-
from odoo import models, fields
EXTS = [
    ('crm.lead', 'External Lead Ref'),
    ('res.partner', 'External Partner Ref'),
    ('res.users', 'External User Ref'),
    ('crm.team', 'External Team Ref'),
    ('crm.stage', 'External Stage Ref'),
    ('utm.source', 'External UTM Source Ref'),
    ('utm.campaign', 'External UTM Campaign Ref'),
    ('utm.medium', 'External UTM Medium Ref'),
    ('crm.tag', 'External Tag Ref'),
    ('res.country', 'External Country Ref'),
    ('res.country.state', 'External State Ref'),
    ('res.partner.industry', 'External Industry Ref'),
    ('mail.activity', 'External Activity Ref'),
    ('mail.message', 'External Message Ref'),
    ('crm.lost.reason', 'External Lost Reason Ref'),
]


for model_name, label in EXTS:
    class_name = model_name.replace('.', '_').title().replace('_', '') + 'Ext'
    attrs = {
        '__module__': __name__,
        "external_ref": fields.Char("External Reference", copy=False, index=True),
        "external_id": fields.Integer("External ID", help="ID of the activity in the external system"),
        "external_employee_id": fields.Many2one("res.users", "External Employee"),
        "external_employee_name": fields.Char(string="External Employee Name", copy=False),
        "external_user_id": fields.Integer(string="External User ID", copy=False),
        "external_user_name": fields.Char(string="External User Name", copy=False),
        "is_external_request": fields.Boolean(string="External Request"),
        "is_external_request_create": fields.Boolean(string="External Request create"),
        "is_external_request_write": fields.Boolean(string="External Request write"),
        "is_external_request_unlink": fields.Boolean(string="External Request unlink"),


    }
    type(class_name, (models.Model,), dict({'_inherit': model_name, **attrs}))

