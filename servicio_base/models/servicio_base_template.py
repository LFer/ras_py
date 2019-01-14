# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ServiceTemplate(models.Model):
    _name = "service.template"
    _description = "Plantilla de Servicios"

    @api.multi
    def _get_operation_type(self):
        operation_national = [('transit_nat', 'Transito Nacional'), ('impo_nat', 'IMPO Nacional'), ('expo_nat', 'EXPO Nacional'), ('interno_plaza_nat', 'Interno Plaza Nacional'), ('interno_fiscal_nat', 'Interno Fiscal Nacional')]
        operation_international = [('transit_inter', 'Transito Internacional'), ('impo_inter', 'IMPO Internacional'), ('expo_inter', 'EXPO Internacional'), ('interno_plaza_inter', 'Interno Plaza Internacional'), ('interno_fiscal_inter', 'Interno Fiscal Internacional')]
        both = operation_national + operation_international
        return both

    name = fields.Char(string='Nombre')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Solicitante del viaje', domain=[('customer', '=', True), ('dispatcher', '=', False)], required=True)
    partner_invoice_id = fields.Many2one(comodel_name='res.partner', string='Cliente a facturar', domain=[('customer', '=', True)])
    partner_dispatcher_id = fields.Many2one(comodel_name='res.partner', string='Despachante', domain=[('dispatcher', '=', True)], required=True)
    pricelist_id = fields.Many2one(comodel_name='product.pricelist.item', string='Tarifa')
    regimen = fields.Selection(_get_operation_type, string="Regimen", store=True)
    currency_id = fields.Many2one(comodel_name="res.currency", string="Moneda", related="pricelist_id.currency_id",index=True, readonly=True, store=True)
    active = fields.Boolean(default=True)
    carga_template_ids = fields.One2many('service.carga.template', 'service_template_id', string='Cargas')


class ServiceCargaTemplate(models.Model):
    _name = "service.carga.template"
    _description = "Plantilla de Cargas de servicio"

    service_template_id = fields.Many2one(comodel_name='service.template')
    name = fields.Char(string='Referencia')
    load_type = fields.Selection([('bulk', 'Bulk'), ('contenedor', 'Contenedor'), ('liquido_granel', u'Granel Líquido'), ('solido_granel', u'Granel Solido')], string='Tipo de Carga')
    load_presentation = fields.Selection([('pallet', 'Pallet'), ('paquete', 'Paquete'), ('otros', 'Otros')], string=u'Presentación')
    pallet_type = fields.Selection([('euro', 'Europeo'), ('merco', 'Mercosur')], string=u'Tipo Pallet')
    importe = fields.Float(string='Valor de Venta')
    currency_id = fields.Many2one(comodel_name="res.currency", string="Moneda")
    producto_servicio_template_ids = fields.One2many('service.productos.template', 'carga_template_id', string='Servicios')


class ServiceProductosTemplate(models.Model):
    _name = "service.productos.template"
    _description = "Plantilla de Servicios Prestados a la carga"

    name = fields.Char(string='Nombre')
    carga_template_id = fields.Many2one(comodel_name='service.carga.template')
    product_id = fields.Many2one(comodel_name='product.product', string='Servicio', domain=[('product_tmpl_id.type', '=', 'service'), ('sale_ok', '=', True)], required=True, change_default=True, ondelete='restrict')
    action_type = fields.Selection([
                                    ('documentation', 'Documentación'),
                                    ('retreat', 'Retiro'),
                                    ('delivery', 'Entrega'),
                                    ('devolution', 'Devolución'),
                                    ('load', u'Carga en Depósito'),
                                    ('beach', 'Playa'),
                                    ('invoice', u'Facturación'),
                                    ('balance', 'Balanza'),
                                    ('customs', 'Aduana'),
                                    ('final_customs', 'Aduana Destino'),
                                    ('seal', 'Precinto'),
                                    ('frontier', 'Liberación Frontera'),
                                    ('fiscal', 'Liberación Fiscal'),
                                    ('deposito', 'Depósito'),
                                ], u'Tipo de Acción')

    location_type = fields.Selection([
                                    ('customs', 'Aduana'),
                                    ('final_customs', 'Aduana Destino'),
                                    ('port', 'Puerto'),
                                    ('terminal', 'Terminal'),
                                    ('deposit', u'Depósito'),
                                    ('airport', 'Aeropuerto'),
                                    ('ministries', 'Ministerio'),
                                    ('trade_zone', 'Zona Franca'),
                                    ('other', 'Otro')
                                ], string='Tipo de Ubicación')

    currency_id = fields.Many2one(comodel_name='res.currency', string='Moneda')
    driver_commission = fields.Float('Comisión de chofer')
    importe = fields.Float(string='Valor de Venta', currency_field='currency_id')
    valor_compra = fields.Monetary(string='Valor Compra', currency_field='currency_id')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Proveedor', domain=[('customer', '=', True)], required=True)