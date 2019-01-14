# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
import ipdb

class Pricelist(models.Model):
    _inherit = "product.pricelist"
    _description = "Pricelist"
    _order = "sequence asc, id desc"

    def _get_default_item_ids(self):
        ProductPricelistItem = self.env['product.pricelist.item']
        vals = ProductPricelistItem.default_get(list(ProductPricelistItem._fields))
        vals.update(compute_price='formula')
        #return [[0, False, vals]]
        return False

    item_ids = fields.One2many('product.pricelist.item', 'pricelist_id', 'Pricelist Items',copy=True, default=_get_default_item_ids)
    country_ids = fields.Many2many('res.partner')





class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    load_type = fields.Selection([('bulk', 'Bulk'), ('contenedor', 'Contenedor'), ('horas', u'Horas')], string='Tipo de Carga')
    horas_espera = fields.Selection([('si', 'Si'), ('no', 'No')], string='Horas de Espera')
    horas_libres = fields.Float(string='Horas Libres')
    sale_price = fields.Float(string='Precio de Venta')
    comision_chofer = fields.Float(string='Comisión Chofer')
    comision_vendedor = fields.Float(string='Comisión Vendedor')
    container_size = fields.Float(string='Tamaño de Contenedor')
    kg_from = fields.Float(string='Hasta Kg')
    kg_to = fields.Float(string='Peso desde Kg')
    volumen_desde = fields.Float(string='Volumen Desde')
    volumen_hasta = fields.Float(string='Volumen Hasta')
    currency_id = fields.Many2one(comodel_name='res.currency', default=46)
    #Campos Nuevos
    sequence = fields.Integer('Secuencia', required=True, help="Da el orden en que se verifican los elementos de la lista de precios. La evaluación otorga la mayor prioridad a la secuencia más baja y se detiene tan pronto como se encuentra un elemento coincidente.")
    hours_from = fields.Float('Hours From')
    hours_to = fields.Float('Hours To')
    wage_from = fields.Float('Wage From')
    wage_to = fields.Float('Wage To')
    mt3_from = fields.Float('MT3 From')
    mt3_to = fields.Float('MT3 To')
    size_from = fields.Float('Size From')
    size_to = fields.Float('Size To')
    wait_hours_from = fields.Float("Waiting hours From")
    wait_hours_to = fields.Float("Waiting hours To")
    wait_value = fields.Float("Value of Wait Time")
    origin_dir = fields.Many2one(comodel_name='res.partner.address.ext',  string='Origen', ondelete='restrict')
    destiny_dir = fields.Many2one(comodel_name='res.partner.address.ext',  string='Destino', ondelete='restrict')
    km_from = fields.Float('Km From')
    km_to = fields.Float('Km To')
    description = fields.Text('Additional information')
    comision_vendedor_currency_id = fields.Many2one('res.currency', 'Moneda')
    comision_chofer_currency_id = fields.Many2one('res.currency', 'Moneda')
    origin_type = fields.Selection([('gen', 'Genérico'), ('spec', 'Específico')], string='Tipo de Origen')



    @api.onchange('load_type')
    def _onchange_product_id(self):
        domain = {}
        if not self.pricelist_id:
            return

        part = self.pricelist_id.partner_id
        if not part:
            warning = {
                'title': ('¡Alerta!'),
                'message': ('Debe definir un cliente primero'),
            }
            return {'warning': warning}
        curr = self.pricelist_id.currency_id
        if not curr:
            warning = {
                'title': ('¡Alerta!'),
                'message': ('Debe definir una moneda primero'),
            }
            return {'warning': warning}
