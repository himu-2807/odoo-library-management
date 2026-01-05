from odoo import models, fields, api
from odoo.exceptions import UserError

class ForceStopBorrowWizard(models.TransientModel):
    _name = "force.stop.borrow.wizard"
    _description = "Force Close Borrow Wizard"

    borrow_id = fields.Many2one(
        "library.borrow",
        string="Borrow Record",
        required=True,
        readonly=True
    )

    def action_force_close(self):
        self.ensure_one()

        if self.borrow_id.status == "returned":
            raise UserError("This borrow is already closed.")

        self.borrow_id.write({
            "status": "returned",
            "return_date": fields.Date.today()
        })
