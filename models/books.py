from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class LibBooks(models.Model):
    _name = "library.book"
    _description = "Library Book"

    # Basic fields
    name = fields.Char(string="Book Name", required=True)
    publish_date = fields.Date(string="Publish Date")
    available = fields.Boolean(string="Available",default=True)
    price = fields.Float(string="Price")
    pages = fields.Integer(string="Pages")
    active = fields.Boolean(default=True)

    author_id = fields.Many2one("res.partner", string="Author")
    category_id = fields.Many2many("library.category", string="Category")
    borrow_ids = fields.One2many(
        "library.borrow", "book_id", string="Borrow History"
    )

    # Smart button
    borrow_count = fields.Integer(
        string="Borrow Count", compute="_compute_borrow_count"
    )

    book_code=fields.Char(string="Book sequence",readonly=True,copy=False,default="New")

    #This model will add the sequence number update we will create new data
    @api.model
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get("book_code","New")=="New":
                vals["book_code"]=self.env["ir.sequence"].next_by_code("library.book") 
        return super().create(vals_list)

    #This compute method shows the no. of book borrowed
    def _compute_borrow_count(self):
        for book in self:
            book.borrow_count = len(book.borrow_ids)

    #Action method written for smart button which shows borrow history
    def action_open_borrow_history(self):
        self.ensure_one()
        return {
            "name": "Borrow History",
            "type": "ir.actions.act_window",
            "res_model": "library.borrow",
            "view_mode": "list,form",
            "domain": [("book_id", "=", self.id)],
            "context": {"default_book_id": self.id},
        }

class LibraryCategory(models.Model):
    _name = "library.category"
    _description = "Library Category"

    name = fields.Char(required=True)


class LibraryBorrow(models.Model):
    _name = "library.borrow"
    _description = "Library Borrow Records"

    member_id = fields.Many2one("library.member", string="Member", required=True)
    book_id = fields.Many2one("library.book", string="Book", required=True)
    borrow_date = fields.Date(string="Borrow Date", default=fields.Date.today)
    return_date = fields.Date(string="Return Date")
    active = fields.Boolean(default=True)

    status = fields.Selection(
        [
            ("borrowed", "Borrowed"),
            ("returned", "Returned"),
        ],
        default="borrowed",
        string="Status",
    )

    #This method will update available to false if some user has borrowed the book
    #this will update the db
    @api.model
    def create(self,vals):
        record=super().create(vals)

        if record.status=="borrowed" and record.book_id:
            record.book_id.write({"available":False})
        return record

    #this is method which updates the database when borrowed book is returned
    def write(self,vals):
        result=super().write(vals)

        if vals.get("status")=="returned":
            for rec in self:
                if rec.book_id:
                    rec.book_id.available=True
        return result

    # this function calculates fines Rs.10/day after 14 days of borrowed date
    # Renders only in UI. No db-level changes

    def write(self, vals):
        res = super().write(vals)

        for rec in self:
            # Check only when book is returned
            if vals.get("status") == "returned" and rec.return_date and rec.borrow_date:
                allowed_days = 14
                fine_per_day = 10

                due_date = rec.borrow_date + timedelta(days=allowed_days)

                if rec.return_date > due_date:
                    late_days = (rec.return_date - due_date).days
                    fine_amount = late_days * fine_per_day

                    # Avoid duplicate unpaid fine
                    existing_fine = self.env["library.fine"].search([
                        ("borrow_id", "=", rec.id),
                        ("status", "=", "unpaid")
                    ], limit=1)

                    if not existing_fine:
                        self.env["library.fine"].create({
                            "member_id": rec.member_id.id,
                            "borrow_id": rec.id,
                            "amount": fine_amount,
                            "status": "unpaid",
                        })

        return res


    # Return date validation
    @api.constrains("borrow_date", "return_date")
    def _check_return_date(self):
        for rec in self:
            if rec.borrow_date and rec.return_date:
                if rec.return_date < rec.borrow_date:
                    raise ValidationError(
                        "Return date cannot be earlier than borrow date."
                    )

    # Same member cannot borrow same book twice
    @api.constrains("book_id", "member_id", "status")
    def _check_same_user_same_book(self):
        for rec in self:
            if not rec.member_id or not rec.book_id:
                continue

            if rec.status == "borrowed":
                domain = [
                    ("book_id", "=", rec.book_id.id),
                    ("member_id", "=", rec.member_id.id),
                    ("status", "=", "borrowed"),
                    ("id", "!=", rec.id),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        "You have already borrowed this book."
                    )

    # Block borrowing if unpaid fine exists
    @api.constrains("member_id", "status")
    def _check_unpaid_fines(self):
        for rec in self:
            if rec.status != "borrowed":
                continue

            unpaid_fine = self.env["library.fine"].search(
                [
                    ("member_id", "=", rec.member_id.id),
                    ("status", "=", "unpaid"),
                ],
                limit=1,
            )

            if unpaid_fine:
                raise ValidationError(
                    "This member has unpaid fines. Please clear them before borrowing another book."
                )

    #shows popup if book is not available
    @api.onchange("book_id")
    def _onchange_book_id(self):
        if self.book_id and not self.book_id.available:
            self.book_id = False
            return {
                "warning": {
                    "title": "Book not available",
                    "message": "This book is currently not available"
                }
            }

    #shows the member name when member is borrowing book from his/her borrow history
    @api.model
    def _default_get(self,field_list):
        res=super()._default_get(field_list)

        if self.env.context.get("default_member_id"):
            res["member_id"]=self.env.context("default_member_id")

        res.update({
            "fine_date":fields.Date.today,
            "status":"unpaid"
            })
