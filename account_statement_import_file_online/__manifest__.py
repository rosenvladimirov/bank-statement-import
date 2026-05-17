# Copyright 2026 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Bank Statement Import: File → Online redirect",
    "version": "19.0.1.0.0",
    "category": "Banking addons",
    "license": "AGPL-3",
    "summary": "When a journal has an online statement provider, the "
               "file-upload import is replaced by a direct provider pull.",
    "author": "Rosen Vladimirov",
    "website": "https://github.com/rosenvladimirov/bank-statement-import",
    "depends": [
        "account_statement_import_file",
        "account_statement_import_online",
    ],
    "data": [],
    "installable": True,
    # Glue module — meaningful only when both hosts are present.
    "auto_install": True,
}
