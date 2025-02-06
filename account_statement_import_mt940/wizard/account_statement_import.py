import io
import logging

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import mt940
    from mt940 import tags
except ImportError:
    _logger.debug("mt-940 not found.")
    mt940 = None


class ProCreditStatementNumber(tags.Tag):
    """Statement number / sequence number

    Pattern: 10n + /
    """

    id = 28
    pattern = r"""
    (?P<statement_number>[\d/]{1,10})  # 10n + /
    $"""


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    @api.model
    def _check_mt940(self, data_file):
        if not mt940:
            return []
        try:
            # tag_parser = ProCreditStatementNumber()
            # mt940_parser = mt940.models.Transactions(tags={tag_parser.id: tag_parser})
            data = io.BytesIO(data_file).read().decode("utf-8")
            # mt940_transactions = mt940_parser.parse(data)
            mt940_transactions = mt940.parse(data)
        except Exception as e:
            _logger.debug(e)
            return []
        return mt940_transactions

    @api.model
    def _get_detail_data(self, transaction_details):
        res = {}
        for detail in transaction_details.split("+"):
            if detail.startswith("21"):
                res.update({"21": detail.replace("21", "")})
            elif detail.startswith("22"):
                detail_row_22 = detail.replace("22", "")
                res.update(
                    {
                        "22": detail_row_22,
                    }
                )
                if len(detail_row_22.split(":")) > 1:
                    detail_row_22_customer = detail_row_22.split(":")
                    detail_row_22_customer_data = dict(
                        zip(detail_row_22_customer[::2], detail_row_22_customer[1::2])
                    )
                    _logger.debug(f"Customer data: {detail_row_22_customer_data}")
            elif detail.startswith("30"):
                res.update(
                    {
                        "30": detail.replace("30", ""),
                    }
                )
            elif detail.startswith("31"):
                res.update(
                    {
                        "31": detail.replace("31", ""),
                    }
                )
            elif detail.startswith("32"):
                res.update(
                    {
                        "32": detail.replace("32", ""),
                    }
                )
            elif detail.startswith("33"):
                res.update(
                    {
                        "33": detail.replace("33", ""),
                    }
                )
        return res

    @api.model
    def _prepare_mt940_transaction_line(self, transaction):
        detail_data = {}
        transaction_details = transaction["transaction_details"]
        detail_data = self._get_detail_data(transaction_details)

        vals = {
            "date": transaction["date"],
            "payment_ref": detail_data.get(
                "21", f"{transaction['customer_reference']}"
            ),
            "amount": float(transaction["amount"].amount),
            "unique_import_id": f"{transaction['id']}"
            f"-{transaction['customer_reference']}",
            "account_number": detail_data.get("31", ""),
            "partner_name": detail_data.get("33", detail_data.get("32", "")),
        }
        return vals

    def _parse_file(self, data_file):
        mt940_transactions = self._check_mt940(data_file)
        if not mt940_transactions:
            return super()._parse_file(data_file)

        result = []
        try:
            transactions = []
            total_amt = 0.00

            mt940_transactions_data = mt940_transactions.data
            for account in mt940_transactions:
                if not account:
                    continue

                vals = self._prepare_mt940_transaction_line(account.data)
                if vals:
                    transactions.append(vals)
                    total_amt += vals["amount"]
            balance = float(
                mt940_transactions_data["final_closing_balance"].amount.amount
            )
            vals_bank_statement = {
                "name": mt940_transactions_data["statement_number"],
                "reference": mt940_transactions_data["transaction_reference"],
                "transactions": transactions,
                "balance_start": balance - total_amt,
                "balance_end_real": balance,
            }
            result.append(
                (
                    mt940_transactions_data["final_opening_balance"].amount.currency,
                    mt940_transactions_data["sequence_number"],
                    [vals_bank_statement],
                )
            )
        except Exception as e:
            raise UserError(
                _(
                    "The following problem occurred during import. "
                    "The file might not be valid.\n\n %s"
                )
                % str(e)
            ) from e
        return result
