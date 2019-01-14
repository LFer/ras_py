# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class DefaultExpenses(models.Model):
    _name = "default.expenses"
    _description = "Default expenses"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', 'Producto', required=True, ondelete="cascade")
    product_qty = fields.Float('Cantidad', default=1)
    partner_parent_id = fields.Many2one('res.partner', 'Empresa', ondelete="cascade")
    product_parent_id = fields.Many2one('product.template', 'Producto', ondelete="cascade")
    vehicle_parent_id = fields.Many2one('fleet.vehicle', 'Vehículo', ondelete="cascade")
    is_outgoing = fields.Boolean(u'¿Es gasto?', default=True)

    _sql_constraints = [
        ('check_product_qty', 'CHECK(product_qty > 0)', "¡Cantidad de producto debe ser mayor que cero!!")]
