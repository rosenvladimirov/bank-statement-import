# Copyright 2026 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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
        """Тегли от свързания провайдер.  Периодът е по същата логика
        като OCA cron-а (`_scheduled_pull`): от последния успешен pull
        (или един интервал назад, ако още няма такъв) до сега.  Когато
        queue_job е installed, `provider._pull` сам отлага реалното
        теглене в background job (виж InfoPay bridge-а) и UI връща
        моментално.
        """
        self.ensure_one()
        provider = self.l10n_bg_provider_id
        date_until = fields.Datetime.now()
        date_since = provider.last_successful_run or (
            date_until - provider._get_next_run_period()
        )
        provider._pull(date_since, date_until)
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_bank_statement_tree"
        )
        action["domain"] = [("journal_id", "=", provider.journal_id.id)]
        return action
