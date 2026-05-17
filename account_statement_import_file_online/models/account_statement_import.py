# Copyright 2026 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    # base модулът декларира това поле required=True; при журнал с
    # провайдер няма файл за качване, затова разхлабваме hard required
    # и валидираме контекстно в import_file_button.
    statement_file = fields.Binary(required=False)

    l10n_bg_provider_id = fields.Many2one(
        "online.bank.statement.provider",
        string="Online Provider",
        compute="_compute_l10n_bg_provider_id",
        help="Online bank statement provider linked to the journal this "
             "import wizard was opened from (resolved from the "
             "journal_id context key set by the dashboard button).",
    )

    @api.depends_context("journal_id")
    def _compute_l10n_bg_provider_id(self):
        jid = self.env.context.get("journal_id")
        journal = (
            self.env["account.journal"].browse(jid)
            if jid
            else self.env["account.journal"]
        )
        provider = (
            journal.online_bank_statement_provider_id if journal else False
        )
        for rec in self:
            rec.l10n_bg_provider_id = provider

    def import_file_button(self):
        """Ако журналът има конфигуриран online provider — същият бутон
        „Import" дърпа от провайдера (без файл).  Иначе → стандартното
        файлово импортиране (super).
        """
        self.ensure_one()
        if self.l10n_bg_provider_id:
            return self._l10n_bg_pull_from_provider()
        if not self.statement_file:
            raise UserError(
                self.env._("Please select a bank statement file to import.")
            )
        return super().import_file_button()

    def _l10n_bg_pull_from_provider(self):
        """Тегли от свързания провайдер.

        Първо натискане за журнала (още няма извлечения) → **backfill**
        от началото на текущата година + anchor-нати начално/крайно
        салдо.  Следващи натискания (вече има извлечения) →
        **incremental** от последното извлечение нататък, без populate
        (OCA верижи balance_start от предходното).

        Решението е по наличие на извлечения, НЕ по
        ``last_successful_run`` — OCA го пише само при scheduled cron
        (``_pull``: ``if is_scheduled``), ръчният бутон никога; това е
        и същият сигнал като bridge-а (``has_prev``), за да се изравнят.

        Когато queue_job е installed, ``provider._pull`` сам отлага
        реалното теглене в background job (InfoPay bridge) и UI връща
        моментално; populate флаговете оцеляват job serialization през
        ``_job_prepare_context_before_enqueue_keys``.
        """
        self.ensure_one()
        provider = self.l10n_bg_provider_id
        Statement = self.env["account.bank.statement"]
        date_until = fields.Datetime.now()
        has_statements = bool(
            Statement.search_count(
                [("journal_id", "=", provider.journal_id.id)]
            )
        )
        if has_statements:
            last = Statement.search(
                [("journal_id", "=", provider.journal_id.id)],
                order="date desc",
                limit=1,
            )
            date_since = provider.last_successful_run or datetime.combine(
                last.date, datetime.min.time()
            )
            ctx = {}
        else:
            year = fields.Date.context_today(self).year
            date_since = datetime(year, 1, 1)
            # InfoPay bridge чете тези context флагове в
            # _obtain_statement_data; за други провайдери са безвредни
            # (просто игнорирани).
            ctx = {
                "l10n_bg_infopay_populate_balance_start": True,
                "l10n_bg_infopay_populate_balance_end": True,
            }
        provider.with_context(**ctx)._pull(date_since, date_until)
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_bank_statement_tree"
        )
        action["domain"] = [("journal_id", "=", provider.journal_id.id)]
        return action
