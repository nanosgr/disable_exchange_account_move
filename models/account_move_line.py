# Copyright 2020 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _reconcile_plan_with_sync(self, plan_list, all_amls):
        # In Odoo 18 the main reconciliation flow goes through this method.
        # Injecting no_exchange_difference=True into the context suppresses both
        # the per-partial exchange differences (line 2651) and the full-batch
        # exchange differences (line 2740) that would otherwise be auto-created.
        if self._exchange_difference_disabled():
            self = self.with_context(no_exchange_difference=True)
        return super()._reconcile_plan_with_sync(plan_list, all_amls)

    def _create_reconciliation_partials(self):
        # Legacy method kept for third-party modules that bypass _reconcile_plan.
        partials_vals_list, exchange_data = self._prepare_reconciliation_partials([
            {
                'aml': line,
                'amount_residual': line.amount_residual,
                'amount_residual_currency': line.amount_residual_currency,
            }
            for line in self
        ])
        partials = self.env['account.partial.reconcile'].create(partials_vals_list)

        if not self._exchange_difference_disabled():
            for index, exchange_values in exchange_data.items():
                partials[index].exchange_move_id = self._create_exchange_difference_move(exchange_values)

        return partials

    def _exchange_difference_disabled(self):
        return (
            self.env['ir.config_parameter']
            .sudo()
            .get_param('disable_exchange_difference') == '1'
        )
