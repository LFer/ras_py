# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class Pricelist(models.Model):
    _inherit = "product.pricelist"
    _description = "Pricelist"
    _order = "sequence asc, id desc"

    partner_id = fields.Many2one(comodel_name='res.partner', string='Cliente')

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    _description = "Pricelist Item"
    _order = "applied_on, min_quantity desc, categ_id desc, id"
    _rec_name = "nombre"

    name = fields.Char(
        'Name', compute='_get_pricelist_item_name_price',
        help="Explicit rule name for this pricelist line.")

    nombre = fields.Char(string='Nombre')

    partner_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', readonly=False)


    @api.one
    @api.depends('categ_id', 'product_tmpl_id', 'product_id', 'compute_price', 'fixed_price', \
        'pricelist_id', 'percent_price', 'price_discount', 'price_surcharge')
    def _get_pricelist_item_name_price(self):
        if self.categ_id:
            self.name = _("Category: %s") % (self.categ_id.name)
        elif self.product_tmpl_id:
            self.name = self.product_tmpl_id.name
        elif self.product_id:
            self.name = self.product_id.display_name.replace('[%s]' % self.product_id.code, '')
        else:
            self.name = _("All Products")

        if self.compute_price == 'fixed':
            self.price = ("%s %s") % (self.fixed_price, self.pricelist_id.currency_id.name)
        elif self.compute_price == 'percentage':
            self.price = _("%s %% discount") % (self.percent_price)
        else:
            self.price = _("%s %% discount and %s surcharge") % (self.price_discount, self.price_surcharge)
        self.name = self.nombre