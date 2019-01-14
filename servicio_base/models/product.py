# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    bse = fields.Boolean('BSE')
    consolidado = fields.Boolean('Consolidado')
    flete = fields.Boolean('Flete')
    is_outgoing = fields.Boolean('¿Es gasto?')
    # invoice_nat_per = fields.Boolean('Porcentaje Nacional', copy=True)
    # invoice_nat_per_amount = fields.Float('Importe Porcentaje Nacional')
    # invoice_nat_per_tax_ids = fields.Many2many('account.tax', 'product_nat_per_tax_rel', 'product_id', 'tax_id', 'Impuestos Nacional', copy=True)
    # invoice_nat_per_account_id = fields.Many2one('account.account', string='Cuenta', domain=[('type', 'not in', ['view', 'closed'])])
    #
    # invoice_int_per = fields.Boolean('Porcentaje Internacional', copy=True)
    # invoice_int_per_amount = fields.Float('Importe Porcentaje Internacional')
    # invoice_int_per_tax_ids = fields.Many2many('account.tax', 'product_int_per_tax_rel', 'product_id', 'tax_id', 'Impuestos Internacional', copy=True)
    # invoice_int_per_account_id = fields.Many2one('account.account', string='Cuenta', domain=[('type', 'not in', ['view', 'closed'])])
