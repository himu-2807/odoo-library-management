from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LibraryFine(models.Model):
	_name="library.fine"
	_description="Library Fine model"

	member_id=fields.Many2one("library.member",string="Member",required=True)
	borrow_id=fields.Many2one("library.borrow",string="Borrowed Record", required=True)
	fine_date=fields.Date(default=fields.Date.today) 
	amount=fields.Float(string="Fine Amount",required=True)
	active = fields.Boolean(default=True)

	status=fields.Selection([('unpaid','Unpaid'),('paid','Paid')],
		string="Status",
		default="unpaid"
		)

	active=fields.Boolean(default=True)

	#This write method will auto archive the member records from fine model when his fine status is changed to paid
	def write(self,vals):
		res=super().write(vals)

		#auto archive fine when paid
		if vals.get("status") == "paid":
			self.filtered(lambda f:f.status=="paid").write({"active":False})

		return res


	#this will restrict the member to borrow another book if fine is pending
	@api.constrains("member_id","borrow_id","status")
	def _check_duplicate_unpaid_fines(self):
		for rec in self:
			if not rec.member_id or not rec.borrow_id:
				continue

			if rec.status == "unpaid":
				domain=[
						("borrow_id", "=", rec.borrow_id.id),
						("member_id", "=", rec.member_id.id),
						("status", "=", "unpaid"),
						("id", "!=", rec.id)
				]

				if self.search_count(domain)>0:
					raise ValidationError("An unpaid fine already exists")


	#This method will show pop-up when admin will delete the record whose fine is still pending
	@api.ondelete(at_uninstall=False)
	def _prevent_book_delete_unpaid_fine(self):
		for rec in self:
			if rec.status=="unpaid":
				raise ValidationError("You cannot delete the record")