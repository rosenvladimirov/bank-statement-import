=============================================
Bank Statement Import: File → Online redirect
=============================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

|badge1|

Glue module between ``account_statement_import_file`` and
``account_statement_import_online``.

When a bank journal has an **online statement provider** configured
(e.g. InfoPay), the journal-dashboard *Import* entry no longer opens
the file-upload wizard.  Instead it triggers a **direct pull** from the
configured provider and shows the resulting bank statements.

Behaviour
=========

``account.journal.import_account_statement()`` is overridden:

* journal **with** ``online_bank_statement_provider_id`` → direct
  ``provider._pull(date_since, date_until)`` where the period mirrors
  the OCA scheduler (``_scheduled_pull``): from ``last_successful_run``
  (or one ``_get_next_run_period()`` back if never run) up to *now*;
* journal **without** a provider → unchanged OCA file-import wizard.

No views, no new models — a pure method override.  ``auto_install`` —
relevant only when both host modules are installed.

Notes
=====

The direct pull does not open the pull wizard, so provider-specific
opt-in flags (such as InfoPay's *populate opening/closing balance*
checkboxes) are not set on this path — the statement chain starts from
the previous statement's closing balance (or zero on a first run).
Use the provider's own pull wizard when an anchored opening balance is
required.

Credits
=======

Authors
~~~~~~~

* Rosen Vladimirov
