# Copyright 2026 Rosen Vladimirov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def import_account_statement(self):
        """Когато журналът има конфигуриран online statement provider,
        file-upload wizard-ът се „угасва" — вместо него директно
        дърпаме извлеченията от провайдера (в нашия случай InfoPay) и
        показваме резултата.  Без провайдер → стандартното OCA
        file-import поведение (super).
        """
        self.ensure_one()
        if self.online_bank_statement_provider_id:
            return self._online_statement_pull_now()
        return super().import_account_statement()

    def _online_statement_pull_now(self):
        """Директен pull от конфигурирания provider — без файл, без
        wizard.  Периодът е по същата логика като OCA cron-а
        (`online.bank.statement.provider._scheduled_pull`): от
        последния успешен pull (или един интервал назад, ако още няма
        такъв) до сега.
        """
        self.ensure_one()
        provider = self.online_bank_statement_provider_id
        date_until = fields.Datetime.now()
        date_since = provider.last_successful_run or (
            date_until - provider._get_next_run_period()
        )
        provider._pull(date_since, date_until)
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_bank_statement_tree"
        )
        action["domain"] = [("journal_id", "=", self.id)]
        return action
