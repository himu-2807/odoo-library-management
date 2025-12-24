from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class LibraryMember(models.Model):
    _name = "library.member"
    _description = "Library Members"

    name = fields.Char(string="Name", required=True)
    phone = fields.Char(string="Phone", required=True)
    email = fields.Char(string="Email Address", required=True)
    membership_date = fields.Date(default=fields.Date.today, string="Membership Date", required=True)
    active = fields.Boolean(string="Active", default=True)

    borrow_ids = fields.One2many("library.borrow","member_id",string="Borrowed Books")
    borrow_count = fields.Integer(string="Borrow Count", compute="_compute_borrow_count")

    fine_ids = fields.One2many("library.fine", "member_id", string="Fines")
    fine_count = fields.Integer(string="Fine Count", compute="_compute_fine_count")

    @api.depends("borrow_ids")
    def _compute_borrow_count(self):
        for member in self:
            member.borrow_count = len(member.borrow_ids)

    @api.depends("fine_ids")
    def _compute_fine_count(self):
        for member in self:
            member.fine_count=len(member.fine_ids)

    @api.constrains("phone")
    def _check_phone(self):
        for rec in self:
            if rec.phone:
                if not rec.phone.isdigit():
                    raise ValidationError("Phone number must be in digit")
                if len(rec.phone)!=10:
                    raise ValidationError("Phone number must be of 10 digits only")

    @api.constrains("email")
    def _check_email(self):
        email_regex=r"^[\w+\.-]+@\w+\.\w+$"
        for rec in self:
            if rec.email and not re.match(email_regex,rec.email):
                raise ValidationError("Please enter valid email")

            if rec.email:
                domain=[
                    ("email", "=", rec.email),
                    ("id", "!=", rec.id)
                ]
                if self.search_count(domain)>0:
                    raise ValidationError("This email already exist")

    def action_open_borrow_history(self):
        self.ensure_one()
        return {
            'name': 'Borrow History',
            'type': 'ir.actions.act_window',
            'res_model': 'library.borrow',
            'view_mode': 'list,form',
            'domain': [('member_id', '=', self.id)],
            'context': {
                'default_member_id': self.id
            }
        }

    def action_open_fines(self):
        self.ensure_one()
        return {
            'name': 'Fines',
            'type': 'ir.actions.act_window',
            'res_model': 'library.fine',
            'view_mode': 'list,form',
            'domain': [('member_id', '=', self.id)],
            'context': {'default_member_id': self.id}
        }
