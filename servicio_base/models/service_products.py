# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import ipdb
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models
_logger = logging.getLogger(__name__)

class rt_service_productos(models.Model):
    _name = "rt.service.productos"
    _description = "Productos"

    @api.model
    def create(self, vals):
        context = self._context
        if context is None:
            context = {}
        if not vals.get('name', False):
            if 'operation_type' in vals and vals['operation_type'] == 'national':
                vals['name'] = self.env['ir.sequence'].next_by_code('rt.servicio.nacional') or '/'
            if 'operation_type' in vals and vals['operation_type'] == 'international':
                vals['name'] = self.env['ir.sequence'].next_by_code('rt.servicio.internacional') or '/'
        return super(rt_service_productos, self).create(vals)

    def _get_duration(self, start, stop):
        """ Get the duration value between the 2 given dates. """
        if start and stop:
            diff = fields.Datetime.from_string(stop) - fields.Datetime.from_string(start)
            if diff:
                duration = float(diff.days) * 24 + (float(diff.seconds) / 3600)
                return round(duration, 2)
            return 0.0

    def _get_field_names(self):
        return False

    # @api.multi
    # @api.onchange('product_id')
    # @api.depends('driver_commission')#aca le meto cualquier fruta, porque parece ser qeu si pongo el campo que deberia disparar el calculo, no me da bola
    # def _compute_commissions(self):
    #     for rec in self:
    #         carpeta = rec.rt_service_id
    #         rec.currency_id = carpeta.currency_id.id
    #         rec.importe = carpeta.pricelist_id.sale_price
    #         rec.driver_commission = carpeta.pricelist_id.comision_chofer
    #         rec.partner_seller_id = carpeta.partner_invoice_id.user_id.partner_id.id

    @api.multi
    def _tree_color(self):
        if not self._ids:
            return ""
        if not isinstance(self._ids, (list,)):
            ids = [self._ids[0]]
        res = dict.fromkeys(ids, 0)
        for record in self.browse(ids):
            if not record.state:
                return ""
            if record.state in ('draft', 'confirm'):
                tree_color = "gold"
            elif record.state in ('draft', 'confirm'):
                tree_color = "orange"
            elif record.state in ('done'):
                tree_color = "grey"
            elif record.state in ('draft'):
                tree_color = "blue"
            elif record.state in ('cancel'):
                tree_color = "red"
            else:
                tree_color = ""
            res[record.id] = tree_color
        return res

    invoices_ids = fields.One2many('account.invoice', 'rt_service_product_id', string='Facturas de Cliente', domain=[('type', '=', 'out_invoice')])
    supplier_invoices_ids = fields.One2many('account.invoice', 'rt_service_product_id', string='Facturas de Cliente',domain=[('type', '=', 'in_invoice')])
    rt_carga_id = fields.Many2one(comodel_name='rt.service.carga', string='Carga Relacioada')
    rt_service_id = fields.Many2one(related='rt_carga_id.rt_service_id', string='Carpeta Relacionada')
    rt_carpeta_id = fields.Many2one(comodel_name='rt.service', string='Carpeta Relacionada')
    operation_type = fields.Selection(related='rt_carga_id.operation_type', string='Tipo de Servicio', readonly=False)
    pricelist_id = fields.Many2one('product.pricelist.item', string='Tarifa')
    regimen = fields.Selection(related='rt_carga_id.regimen', string='Regimen')
    partner_invoice_id = fields.Many2one(related='rt_service_id.partner_invoice_id', string='Cliente a facturar', domain=[('customer', '=', True)], store=True)
    state = fields.Selection(related='rt_carga_id.rt_service_id.state', string='Estado')
    load_type = fields.Selection(related='rt_carga_id.load_type', string='Tipo de Carga')
    name = fields.Char(string='Nombre')
    fecha_fin = fields.Datetime(string='Fin')
    product_type = fields.Selection([('propio', 'Propio'), ('terceros', 'Terceros')], string='Origen del Servicio') #Este campo va determinar muchisimos comportamientos
    product_id = fields.Many2one(comodel_name='product.product', string='Servicio', domain=[('product_tmpl_id.type', '=',  'service'), ('sale_ok', '=', True)], required=False, change_default=True, ondelete='restrict')
    matricula = fields.Char(string=u'Matricula')
    matricula_dos = fields.Char(string=u'Matricula Dos')
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', string=u'Matrícula')
    vehicle_type = fields.Selection(related='vehicle_id.vehicle_type', type='char', readonly=True)
    driver_id = fields.Many2one('hr.employee', 'Chofer', help=u'Chofer del Vehículo')
    driver_commission = fields.Float('Comisión de chofer')
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
    origin_id = fields.Many2one(comodel_name='res.partner.address.ext', string='Origen')
    destiny_id = fields.Many2one(comodel_name='res.partner.address.ext', string='Destino')


    partner_seller_id = fields.Many2one(comodel_name='res.partner', string='Vendedor', domain=[('seller', '=', True)], readonly=True)


    partner_id = fields.Many2one(comodel_name='res.partner', string='Proveedor', domain=[('supplier', '=', True)])
    importe = fields.Float(string='Valor de Venta')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Moneda')
    costo_estimado = fields.Monetary(string='Costo Estimado', currency_field='currency_id')
    valor_compra = fields.Monetary(string='Valor Compra', currency_field='currency_id')
    invoiced = fields.Boolean(string='Es para saber si este servicio ya fue facturado o no')
    invoiced_supplier = fields.Boolean(string='Es para saber si este servicio ya fue facturado o no')
    tree_color = fields.Char(compute=_tree_color, string='Tree Color', type='char', store=False)
    provision_creada = fields.Boolean(string='Para saber si se creo o no la provision para este servicio')
    #Para la vista calendario
    start = fields.Datetime('Inicio', required=True, help="Start date of an event, without time for full days events")
    stop = fields.Datetime('Stop', required=True, help="Stop date of an event, without time for full days events")
    allday = fields.Boolean('All Day', default=False)
    start_datetime = fields.Datetime('Start DateTime', compute='_compute_dates', inverse='_inverse_dates', store=True, states={'done': [('readonly', True)]}, track_visibility='onchange')
    stop_date = fields.Date('End Date', compute='_compute_dates', inverse='_inverse_dates', store=True, states={'done': [('readonly', True)]}, track_visibility='onchange')
    stop_datetime = fields.Datetime('End Datetime', compute='_compute_dates', inverse='_inverse_dates', store=True, states={'done': [('readonly', True)]}, track_visibility='onchange')  # old date_deadline
    duration = fields.Float('Duration', states={'done': [('readonly', True)]})
    cliente_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    seller_commission = fields.Float(string='Comisión Vendedor')
    #pricelist_id = fields.Many2one('product.pricelist')
    fletero_id = fields.Many2one('res.partner', 'Fletero', domain=[('freighter', '=', True)])
    matricula_fletero = fields.Char(string='Matricula Fletero')
    #Facturable
    is_invoiced = fields.Boolean('Facturable', help='Marque esta casilla si este servicio no se factura')
    # Es Gasto
    is_outgoing = fields.Boolean('¿Es Gasto?', help='Marque esta casilla si este servicio es un Gasto')

    @api.onchange('product_type', 'pricelist_id')
    def _onchange_product_type(self):
        res = {}
        warning = {}
        if self.product_type:
            place_obj = self.env['res.partner.address.ext']
            self.currency_id = self.rt_carga_id.rt_service_id.currency_id.id
            self.partner_seller_id = self.rt_carga_id.rt_service_id.partner_invoice_id.user_id.partner_id.id
            pricelist_item = self.rt_carga_id.pricelist_id
            if pricelist_item:
                self.pricelist_id = pricelist_item.id
                if len(pricelist_item) >= 2:
                    #Por ahora dejamos vacio
                    self.importe = pricelist_item[0].sale_price
                    self.driver_commission = pricelist_item[0].comision_chofer
                    self.seller_commission = pricelist_item[0].comision_vendedor
                else:
                    self.importe = pricelist_item.sale_price
                    self.driver_commission = pricelist_item.comision_chofer
                    self.seller_commission = pricelist_item.comision_vendedor



            #self.currency_id = self.pr
            # if self.product_type == 'terceros':
            #     self.valor_compra = self.pricelist_id.cost_price

            partner_id = self.partner_invoice_id.id
            places = place_obj.search([('partner_id', '=', partner_id)])

            # if not places:
            #     warning = {
            #         'title': ("Alerta para %s") % self.partner_invoice_id.name,
            #         'message': "No se encontró Lugar para el cliente"
            #         }
            #
            # domain = {'origin_id': [('id', 'in', places.ids)], 'destiny_id': [('id', 'in', places.ids)]}

            # if warning:
            #     res['warning'] = warning
            # if domain:
            #     res['domain'] = domain
        return res

    @api.onchange('cliente_id', 'rt_carpeta_id')
    def _onchange_cliente_id(self):
        res = {}
        folder_obj = self.env['rt.service']
        carga_obj = self.env['rt.service.carga']
        cargas = []
        ctx = self._context.copy()
        cliente = False
        folder_id = False
        if self.cliente_id:
            cliente = self.cliente_id.id


        if 'is_from_calendar_view' in ctx:
            folders = folder_obj.search([('partner_invoice_id', '=', cliente)])
            domain = {'rt_carpeta_id': [('id', 'in', folders.ids)]}

            if self.rt_carpeta_id:
                cargas = self.rt_carpeta_id.carga_ids.ids
                domain['rt_carga_id'] = [('id', 'in', cargas)]

            if domain:
                res['domain'] = domain
        return res



    @api.multi
    @api.depends('allday', 'start', 'stop')
    def _compute_dates(self):
        for record in self:
            if record.allday and record.start and record.stop:
                record.start_date = record.start.date()
                record.start_datetime = False
                record.stop_date = record.stop.date()
                record.stop_datetime = False

                record.duration = 0.0
            else:
                record.start_date = False
                record.start_datetime = record.start
                record.stop_date = False
                record.stop_datetime = record.stop

                record.duration = self._get_duration(record.start, record.stop)


    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        for rec in self:
            if not rec.vehicle_id:
                return
            rec.driver_id = rec.vehicle_id.driver_id.id


    @api.multi
    def _inverse_dates(self):
        pass
        # for record in self:
        #     if record.allday:
        #
        #         # Convention break:
        #         # stop and start are NOT in UTC in allday event
        #         # in this case, they actually represent a date
        #         # i.e. Christmas is on 25/12 for everyone
        #         # even if people don't celebrate it simultaneously
        #         enddate = fields.Datetime.from_string(record.stop_date)
        #         enddate = enddate.replace(hour=18)
        #
        #         startdate = fields.Datetime.from_string(record.start_date)
        #         startdate = startdate.replace(hour=8)  # Set 8 AM
        #
        #         record.write({
        #             'start': startdate.replace(tzinfo=None),
        #             'stop': enddate.replace(tzinfo=None)
        #         })
        #     else:
        #         record.write({'start': record.start_datetime,
        #                        'stop': record.stop_datetime})

rt_service_productos()