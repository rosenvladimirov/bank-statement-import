# Copyright 2026 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Bank Statement Import: File → Online provider",
    "version": "18.0.1.2.0",
    "category": "Banking addons",
    "license": "AGPL-3",
    "summary": "On the file-import wizard, when the journal has an online "
               "statement provider, hide the file upload, show the "
               "provider and let the Import button pull from it.",
    "author": "Rosen Vladimirov",
    "website": "https://github.com/rosenvladimirov/bank-statement-import",
    "depends": [
        "account_statement_import_file",
        "account_statement_import_online",
    ],
    "data": [
        "views/account_statement_import_view.xml",
    ],
    "installable": True,
    # Glue module — meaningful only when both hosts are present.
    "auto_install": True,
}
