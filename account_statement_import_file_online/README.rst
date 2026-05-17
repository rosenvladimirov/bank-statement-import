=============================================
Bank Statement Import: File → Online provider
=============================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

|badge1|

Glue module between ``account_statement_import_file`` and
``account_statement_import_online``.

On the standard **file-import wizard** (``account.statement.import``),
when the journal it was opened from has an **online statement
provider** configured (e.g. InfoPay):

* the file-upload field and the "supported formats" text are hidden;
* an info banner shows which provider is linked;
* the existing **Import and View** button pulls the statements from
  that provider instead of parsing an uploaded file.

The wizard still opens normally — nothing is bypassed; the operator
simply sees that a provider is configured and presses *Import*.

Behaviour
=========

* ``account.statement.import`` is extended with a computed
  ``l10n_bg_provider_id`` (resolved from the ``journal_id`` context
  key the dashboard button sets).
* ``import_file_button()`` is overridden: with a provider → pull from
  it; without a provider → unchanged file import (a clear error is
  raised if no file was selected).
* Pull period: **first press for the journal** (no statements yet) →
  *backfill* from Jan 1 of the current year with the opening/closing
  balance anchor flags set; **subsequent presses** → *incremental*
  from the latest statement onward.  The backfill-vs-incremental
  decision is by statement presence, not ``last_successful_run``
  (OCA only writes the latter on the scheduled cron, never on a
  manual pull) — the same signal the InfoPay bridge uses to anchor.
* ``statement_file`` hard ``required`` is relaxed (validated
  contextually) so the form can be submitted with no file when a
  provider is used.

Notes
=====

The provider pull goes through ``provider._pull``; when ``queue_job``
is installed the InfoPay bridge offloads it to a background job, so
the wizard returns immediately and a toast reports progress.  On the
initial backfill the *populate opening/closing balance* flags are set
so the statement chain is anchored to the real balance; they survive
job serialization via the bridge's
``_job_prepare_context_before_enqueue_keys``.

Credits
=======

Authors
~~~~~~~

* Rosen Vladimirov
