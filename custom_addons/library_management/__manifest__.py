{
    "name": "Library Management",
    "version": "19.0.1.0.0",
    "summary": "Manage library books",
    "description": "Simple library management module to manage books",
    "category": "Education",
    "author": "Admin",
    "license": "LGPL-3",
    "depends": ["base","contacts"],
    "data": [
        "security/ir.model.access.csv",

        "views/library_category_views.xml",
        "views/library_books_views.xml",
        "views/library_member_views.xml",
        "views/library_borrow_views.xml",
        "views/library_fine_views.xml"
    ],
    "installable": True,
    "application": True,
}

