# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import ipdb
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
_logger = logging.getLogger(__name__)


class rt_service(models.Model):
    _name = "rt.service"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Servicio Nacional-Internacional"
    _order = "id DESC"

    @api.model
    def create(self, vals):
        context = self._context
        if context is None:
            context = {}
        if not vals.get('name', False):
            if 'operation_type' in vals and vals['operation_type'] == 'national':
                if vals.get('state', False) == 'draft':
                    vals['name'] = 'Carpeta Nacional Borrador'
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('rt.service.nacional') or '/'

            if 'operation_type' in vals and vals['operation_type'] == 'international':
                if vals.get('state', False) == 'draft':
                    vals['name'] = 'Carpeta Internacional Borrador'
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('rt.service.internacional') or '/'
        return super(rt_service, self).create(vals)


    @api.multi
    def _get_operation_type(self):
        res = []
        operation_national = [('transit_nat', 'Transito Nacional'), ('impo_nat', 'IMPO Nacional'), ('expo_nat', 'EXPO Nacional'), ('interno_plaza_nat', 'Interno Plaza Nacional'), ('interno_fiscal_nat', 'Interno Fiscal Nacional')]
        operation_international = [('transit_inter', 'Transito Internacional'), ('impo_inter', 'IMPO Internacional'), ('expo_inter', 'EXPO Internacional'), ('interno_plaza_inter', 'Interno Plaza Internacional'), ('interno_fiscal_inter', 'Interno Fiscal Internacional')]
        both = operation_national + operation_international
        context = self._context
        if self.regimen:
            print('hacemos algo?')

        elif 'default_operation_type' in context:
            if context['default_operation_type'] == 'national':
                res = operation_national
            if context['default_operation_type'] == 'international':
                res = operation_international
        else:
            return both
        return res

    @api.depends('operation_type')
    def compute_operation_type(self):
        return

    @api.multi
    def get_vehicles(self):
        for carga in self.carga_ids:
            for line in carga.producto_servicio_ids:
                if line.vehicle_id:
                    carga.rt_service_id.vehicles_ids += line.vehicle_id
        return


    service_template_id = fields.Many2one(comodel_name='service.template', string='Plantilla')
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user,track_visibility="onchange")
    invoices_ids = fields.One2many(comodel_name='account.invoice', inverse_name='rt_service_id', string='Facturas de Cliente', domain=[('type', '=', 'out_invoice')])
    operation_type = fields.Selection([('national', 'Nacional'), ('international', 'Internacional')],string='Tipo de Servicio')
    active = fields.Boolean(default=True)
    name = fields.Char('Referencia', required=False, copy=False, select=True, default='/')
    reference = fields.Text(string='Referencia')
    dua_type = fields.Selection([('cabezal', 'En Cabezal'), ('linea', u'Por Línea')], string='Modalidad DUA')
    invoice_type_id = fields.Many2one(comodel_name='rt.invoice.type', string=u'Modalidad de Facturación')
    dua_cabezal = fields.Char(string='DUA')
    rt_servicios_ids = fields.One2many('rt.service.line', 'rt_service_id', string='Servicios Asociados')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirm', 'Confirmado'),
        ('inprocess', 'En proceso'),
        ('progress', 'Servicio Facturado'),
        ('cancel', 'Cancelado'),
        ('done', 'Realizado'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Solicitante del viaje', domain=[('customer', '=', True), ('dispatcher', '=', False)])
    partner_invoice_id = fields.Many2one(comodel_name='res.partner', string='Cliente a facturar', domain=[('customer', '=', True)])
    partner_dispatcher_id = fields.Many2one(comodel_name='res.partner', string='Despachante', domain=[('dispatcher', '=', True)])
    partner_where_paper_id = fields.Many2one('res.partner', 'Donde quedan los papeles', domain=[('where_paper', '=', True)])
    partner_carrier_id = fields.Many2one(comodel_name='res.partner', string='Carrier', domain=[('carrier', '=', True)])
    pricelist_id = fields.Many2one(comodel_name='product.pricelist', string='Tarifa')
    currency_id = fields.Many2one(comodel_name="res.currency", string="Moneda", related="pricelist_id.currency_id", index=True, readonly=True, store=True)
    partner_consignee_id = fields.Many2one(comodel_name='res.partner', string='Consignatario', domain=[('consignee', '=', True)])
    partner_remittent_id = fields.Many2one(comodel_name='res.partner', string=u'Remitente de Tránsito', domain=[('remittent', '=', True)])
    cut_off_doc = fields.Datetime(string='Cut off documentario')
    start_datetime = fields.Datetime(string='Fecha Inicio', required=True, select=True, copy=False, default=fields.datetime.now())
    stop_datetime = fields.Datetime('Fecha Fin', select=True, copy=False)
    regimen = fields.Selection(_get_operation_type, string="Regimen", store=True)
    cut_off_operative = fields.Datetime('Cut off operative', required=False)
    partner_user_zf_id = fields.Many2one('res.partner', 'User of ZF', domain=[('user_zf', '=', True)])
    partner_receiver_id = fields.Many2one('res.partner', 'Receiver', domain=[('receiver', '=', True)])
    partner_dispatcher_from_id = fields.Many2one('res.partner', 'Despachante de Origen',domain=[('dispatcher', '=', True)])
    partner_dispatcher_to_id = fields.Many2one('res.partner', 'Despachante de Destino',domain=[('dispatcher', '=', True)])
    grouping_stock = fields.Char('Stock de agrupamiento', size=16)
    output_reference = fields.Char('Referencia de Salida', size=16)
    detail = fields.Text('Detalle')
    lic_type = fields.Char('Tipo de Permiso')
    ministries = fields.Boolean('Ministerio')
    seller_commission = fields.Float('Comisión del vendedor', digits_compute=dp.get_precision('Account'))
    customs_transit = fields.Boolean('Tránsito Aduanero')
    permissive = fields.Boolean('Permisado')
    peons = fields.Boolean('Peons')
    ministries_date = fields.Datetime('Fecha de Ministerio')
    hoist = fields.Boolean('Montacargas')
    dispatcher_contact = fields.Char('Contacto despachante', size=254)
    load_agent_contact = fields.Char('Contacto Cliente Descarga', size=254)
    dangers_loads = fields.Boolean('Carga Peligrosa')
    #Comision
    travel_commission = fields.Float(string=u'Comisión')
    # Campos Auxiliares
    dua_visible = fields.Boolean('Page DUA')
    mic_visible = fields.Boolean('Page MIC')
    retreat_data_visible = fields.Boolean('Page Travel Flow')
    tack_visible = fields.Boolean('Page Tack')
    other_concept_visible = fields.Boolean('Page Other Concepts')
    simplified_message_visible = fields.Boolean('Page Simplified Message')
    summary_visible = fields.Boolean('Page Summary')
    packing_visible = fields.Boolean('Page Packing')
    extra_invoice_partner_visible = fields.Boolean('Partner Invoices')
    srv_partner_seller_id_visible = fields.Boolean('Seller')
    srv_partner_dispatcher_id_visible = fields.Boolean('Dispatcher')
    srv_partner_where_paper_id_visible = fields.Boolean('Where they are the papers')
    srv_partner_remittent_id_visible = fields.Boolean('Remittent of transit')
    #Carga
    carga_ids = fields.One2many('rt.service.carga', 'rt_service_id', string='Cargas')
    #invoice_lines = fields.Many2many('account.invoice.line', 'invoice_id', 'Invoice Lines', copy=False)
    xls_name = fields.Char(string='File Name', size=128)
    xls_file = fields.Binary(string='XLS File')
    ras_is_carrier = fields.Boolean('Ras es transportista', compute="_get_customer_carrier")
    imo = fields.Boolean('IMO')
    crt = fields.Boolean('CRT')
    container_qty = fields.Integer('Cantidad de contenedores')
    make_page_invisible = fields.Boolean(help='Este booleano es para hacer invisible la pagina si no se cargo regimen, cliente a facturar')
    make_dua_invisible_or_required = fields.Boolean(help='Este campo me va ayudar hacer el dua de las cargas invisible o visible y requerido')
    load_type = fields.Selection([('bulk', 'Bulk'), ('contenedor', 'Contenedor'), ('liquido_granel', u'Granel Líquido'),('solido_granel', u'Granel Solido')], string='Tipo de Carga')
    make_presentacion_invisible = fields.Boolean(help='Esto va hacer el campo presentacion invisible', default=True)
    make_terminal_devolucion_invisible = fields.Boolean(help='Esto hace el campo terminal de devolucion invisible')
    profit_carpeta_ids = fields.One2many('rt.service.profit.carpeta', 'rt_service_id', string='Profit Carpeta')
    profit_carpeta = fields.Float(string='Profit')
    supplier_invoices_ids = fields.One2many('account.invoice', 'rt_service_id', string='Facturas de Cliente',domain=[('type', '=', 'in_invoice')])
    vehicles_ids = fields.One2many('fleet.vehicle', 'rt_service_id', string='Vehículo', compute='get_vehicles')


    @api.multi
    def borrador_confirmado(self):
        vals = {}
        if self.operation_type == 'national':
            vals['name'] = self.env['ir.sequence'].next_by_code('rt.service.nacional') or '/'
            vals['state'] = 'confirm'

        if self.operation_type == 'international':
            vals['name'] = self.env['ir.sequence'].next_by_code('rt.service.internacional') or '/'
            vals['state'] = 'confirm'

        return self.write(vals)

    @api.multi
    def a_cancelado(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def a_borrador(self):
        return self.write({'state': 'draft'})

    @api.multi
    def confirmado_en_procesos(self):
        return self.write({'state': 'inprocess'})





    @api.multi
    @api.depends('name', 'obs')
    def name_get(self):

        return [(rec.id, '%s - %s' % (rec.name, rec.reference)) for rec in self]

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id(self):
        domain = {}
        res = {}
        if not self.partner_invoice_id:
            domain = {'pricelist_id': [('id', 'in', None)]}
        if domain:
            res['domain'] = domain
        return res


    @api.onchange('partner_invoice_id', 'company_id')
    def _onchange_partner_id(self):
        domain = {}
        warning = {}
        res = {}
        pricelist_obj = self.env['product.pricelist']
        if self.partner_invoice_id:
            partner_id = self.partner_invoice_id.id
            pricelist = pricelist_obj.search([('partner_id', '=', partner_id)])

            if not pricelist:
                self.pricelist_id = False
                warning = {
                    'title': _("Alerta para %s") % self.partner_invoice_id.name,
                    'message': "No se encontró Tarifa para el cliente"
                }


            domain = {'pricelist_id': [('id', 'in', pricelist.ids)]}
        if warning:
            res['warning'] = warning
        if domain:
            res['domain'] = domain
        return res


    def _compute_line_data_for_template_change(self, line):
        return {
            'name': line.name,
            'load_type': line.load_type,
        }

    def _compute_line_data_for_template_service(self, line):
        return {
            'name': line.name,
        }

    @api.multi
    @api.onchange('service_template_id')
    def onchange_service_template_id(self):
        if not self.service_template_id:
            return
        template = self.service_template_id.with_context(lang=self.partner_id.lang)
        self.regimen = template.regimen
        self.partner_invoice_id = template.partner_invoice_id.id
        self.pricelist_id = template.pricelist_id.id
        self.partner_id = template.partner_id.id
        self.partner_dispatcher_id = template.partner_dispatcher_id.id
        order_lines = [(5, 0, 0)]
        product_lines = [(5, 0, 0)]
        for line in template.carga_template_ids:
            data = self._compute_line_data_for_template_change(line)
            price = line.importe


            data.update({
                'load_presentation': line.load_presentation,
                'pallet_type': line.pallet_type,
                'importe': price,
                'currency_id': line.currency_id.id,
            })

            order_lines.append((0, 0, data))

            if line.producto_servicio_template_ids:
                for srv in line.producto_servicio_template_ids:
                    data_prod = self._compute_line_data_for_template_service(line)
                    data_prod.update({
                        'product_id': srv.product_id.id,
                        'partner_id': srv.partner_id.id,
                        'importe': srv.importe,
                        'currency_id': srv.currency_id.id,
                        'location_type': srv.location_type,
                        'action_type': srv.action_type,
                        'valor_compra': srv.valor_compra,
                    })
                product_lines.append((0, 0, data_prod))
        self.carga_ids = order_lines

        # for prod in self.carga_ids:
        #     prod.producto_servicio_ids = product_lines

    @api.multi
    def check_dua_fn(self, regimen=False):
        if not regimen:
            regimen = self.regimen
        dua_importaciones = range(0, 500000)
        dua_exportaciones = range(500000, 700000)
        dua_transitos = range(700000, 1000000)
        dua_type = ''
        if self.dua_cabezal:
            # self.make_dua_invisible_or_required = True
            #Primero validamos que este bien ingresado -
            if not '-' in self.dua_cabezal:
                raise Warning('El formato esperado es MES-AÑO-DUA \n ej: 01-2019-124578')
            #14 es el largo esperado de MES-AÑO-DUA = MM-AAAA-XXXXXX
            if len(self.dua_cabezal) == 14:
                #Separamos el dua por '-'
                dua_split = self.dua_cabezal.split('-')
                #tenemos que probar lo ultimo
                dua = dua_split[-1]
                int_dua = int(dua)
                if int_dua not in dua_importaciones and int_dua not in dua_exportaciones and int_dua not in dua_transitos:
                    raise Warning('El número de DUA ingresado no es válido \n El formato esperado es MES-AÑO-DUA \n ej: 01-2019-124578 \n Recuerde: \n 000001 - 499999 - Importaciones \n 500000 - 699999 - Exportaciones \n 700000 - 999999 - Transitos   ')
                if not self.regimen:
                    raise Warning('Debe ingresar el regimen primero')

                if (regimen == 'impo_inter' or regimen == 'impo_nat') and int_dua not in dua_importaciones:
                    if int_dua in dua_exportaciones:
                        dua_type = 'Exportaciones (500000 - 699999)'
                    if int_dua in dua_transitos:
                        dua_type = 'Transitos (700000 - 999999)'

                    raise Warning('DUA inválido para el Regimen IMPO \n El DUA ingresado corresponde al regimen  %s' % dua_type)

                if (regimen == 'expo_inter' or regimen == 'expo_nat') and int_dua not in dua_exportaciones:
                    if int_dua in dua_transitos:
                        dua_type = '700000 - 999999 - Transitos'
                    if int_dua in dua_importaciones:
                        dua_type = '000001 - 499999 - Importaciones'
                    raise Warning('DUA inválido para el Regimen EXPO \n El DUA ingresado corresponde al regimen  %s' % dua_type)

                if (regimen == 'transit_inter' or regimen == 'transit_nat') and int_dua not in dua_transitos:
                    if int_dua in dua_importaciones:
                        dua_type = '000001 - 499999 - Importaciones'
                    if int_dua in dua_exportaciones:
                        dua_type = '500000 - 699999 - Exportaciones'
                    raise Warning('DUA inválido para el Regimen TRANSITO \n El DUA ingresado corresponde al regimen  %s' % dua_type)

    # @api.onchange('dua_type')
    # def _onchange_dua_type(self):
    #     if self.dua_type == 'cabezal':
    #         self.make_dua_invisible_or_required = True
    #     if self.dua_type == 'linea':
    #         self.make_dua_invisible_or_required = False


    @api.multi
    @api.onchange('dua_cabezal')
    def check_dua(self):
        dua_importaciones = range(0, 500000)
        dua_exportaciones = range(500000, 700000)
        dua_transitos = range(700000, 1000000)
        dua_type = ''
        for rec in self:
            if rec.dua_cabezal:
                #Primero validamos que este bien ingresado -
                if not '-' in rec.dua_cabezal:
                    raise Warning('El formato esperado es MES-AÑO-DUA \n ej: 01-2019-124578')
                #14 es el largo esperado de MES-AÑO-DUA = MM-AAAA-XXXXXX
                if len(rec.dua_cabezal) == 14:
                    #Separamos el dua por '-'
                    dua_split = rec.dua_cabezal.split('-')
                    #tenemos que probar lo ultimo
                    dua = dua_split[-1]
                    int_dua = int(dua)
                    if int_dua not in dua_importaciones and int_dua not in dua_exportaciones and int_dua not in dua_transitos:
                        raise Warning('El número de DUA ingresado no es válido \n El formato esperado es MES-AÑO-DUA \n ej: 01-2019-124578 \n Recuerde: \n 000001 - 499999 - Importaciones \n 500000 - 699999 - Exportaciones \n 700000 - 999999 - Transitos   ')
                    if not rec.regimen:
                        raise Warning('Debe ingresar el regimen primero')

                    if (rec.regimen == 'impo_inter' or rec.regimen == 'impo_nat') and int_dua not in dua_importaciones:
                        if int_dua in dua_exportaciones:
                            dua_type = 'Exportaciones (500000 - 699999)'
                        if int_dua in dua_transitos:
                            dua_type = 'Transitos (700000 - 999999)'

                        raise Warning('DUA inválido para el Regimen IMPO \n El DUA ingresado corresponde al regimen  %s' % dua_type)

                    if (rec.regimen == 'expo_inter' or rec.regimen == 'expo_nat') and int_dua not in dua_exportaciones:
                        if int_dua in dua_transitos:
                            dua_type = '700000 - 999999 - Transitos'
                        if int_dua in dua_importaciones:
                            dua_type = '000001 - 499999 - Importaciones'
                        raise Warning('DUA inválido para el Regimen EXPO \n El DUA ingresado corresponde al regimen  %s' % dua_type)

                    if (rec.regimen == 'transit_inter' or rec.regimen == 'transit_nat') and int_dua not in dua_transitos:
                        if int_dua in dua_importaciones:
                            dua_type = '000001 - 499999 - Importaciones'
                        if int_dua in dua_exportaciones:
                            dua_type = '500000 - 699999 - Exportaciones'
                        raise Warning('DUA inválido para el Regimen TRANSITO \n El DUA ingresado corresponde al regimen  %s' % dua_type)

    @api.multi
    def write(self, values):
        #Chequeamos el dua
        regimen = False
        if 'regimen' in values:
            regimen = values['regimen']
        self.check_dua_fn(regimen=regimen)
        res = super(rt_service, self).write(values)
        return res



    @api.multi
    def action_open_invoice_wzd(self):
        row = self
        # pdb.set_trace()
        if not row.ready_to_invoice:
            raise Warning(_('Error'), _("This service not have any invoiceable product pendant to invoice.\n Please check the 'Invoiceable' field on each service product that you want to invoice."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice Order'),
            'res_model': 'rt.service.advance.payment.inv',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_nat_per_tax_ids': [
                    (6, 0, [ac_tax.id for ac_tax in row.invoice_nat_per_tax_ids if row.invoice_nat_per_tax_ids])],
                'invoice_nat_per_amount': row.invoice_nat_per_amount,
                'default_invoice_nat_per_account_id': row.invoice_nat_per_account_id and row.invoice_nat_per_account_id.id or False,
                'default_invoice_int_per_tax_ids': [
                    (6, 0, [ac_tax.id for ac_tax in row.invoice_int_per_tax_ids if row.invoice_int_per_tax_ids])],
                'invoice_int_per_amount': row.invoice_int_per_amount,
                'default_invoice_int_per_account_id': row.invoice_int_per_account_id and row.invoice_int_per_account_id.id or False,
            }
        }




    @api.multi
    def crea_provision(self, monto, proveedor, producto, moneda, servicio):
        lineas = []
        taxes = producto.supplier_taxes_id
        provision_obj = self.env['expense.provision']
        line_dict = {
            'product_id': producto.id,
            'account_id': 1,
            'quantity': 1,
            'price_unit': monto,
            'provision_line_tax_ids': [(6, 0, taxes.ids)],
            'price_subtotal': monto * 1,
            'price_total': moneda.id,
            'name': self.name,



        }
        lineas.append((0, 0, line_dict))
        provision = provision_obj.create({
            'name': self.name,
            'partner_id': proveedor.id,
            'date_invoice': fields.Date.context_today(self),
            'currency_id': moneda.id,
            'account_id': proveedor.property_account_payable_id.id,
            'rt_service_product_id':servicio.id,
            'expense_line_ids': lineas
        })
        provision._onchange_invoice_line_ids()
        provision._compute_amount()

        return

    @api.onchange('regimen', 'partner_invoice_id', 'dua_type')
    def onchange_fields(self):
        for rec in self:
            if rec.dua_cabezal:
                rec.make_dua_invisible_or_required = True
            if not rec.regimen or not rec.partner_invoice_id or not rec.dua_type:
                rec.make_page_invisible = True
            elif rec.regimen or rec.partner_invoice_id or rec.dua_type:
                rec.make_page_invisible = False
            else:
                rec.make_page_invisible = True
            if rec.regimen:
                if rec.regimen == 'expo':
                    rec.make_terminal_devolucion_invisible = False
        return

    def crea_carga_fcl(self, modelo, cantidad):
        line_vals = {}
        lineas = []
        pricelist = self.pricelist_id
        for line in range(int(cantidad)):
            vals = {
                'rt_service_id':self.id,
                'name' : '/',
                'load_type': 'contenedor',
                'container_type': modelo.id,
                'container_size': modelo.size,
                'make_dua_invisible_or_required': True if self.dua_cabezal else False,
                #'importe': pricelist.sale_price,
                #'importe': pricelist.item_ids[0].sale_price,
                'partner_seller_id': self.partner_invoice_id.user_id.partner_id.id,
                'importe_currency_id': pricelist.currency_id.id,
                'partner_invoice_id': self.partner_invoice_id.id,

            }
            lineas.append((0, 0, vals))

        line_vals['carga_ids'] = lineas

        return line_vals

    @api.multi
    def generar_cargas(self):

        if not self.rt_servicios_ids:
            raise Warning('Debe ingresar lineas')
        for line in self.rt_servicios_ids:
            if not line.service_type_id:
                raise Warning('Debe selecionar el tipo de servicio')
            if not line.vehicle_id:
                raise Warning('Debe selecionar el modelo')
            if not line.qty:
                raise Warning('La cantidad no puede ser 0')

            #Por ahora vamos por nombre, tenemos que encontrar una forma mas elegante de hacerlo
            if line.service_type_id.name == 'FCL':
                vals = self.crea_carga_fcl(modelo=line.vehicle_id, cantidad=line.qty)
                self.write(vals)


    @api.multi
    def generar_provisiones(self):
        """
        Para cada servicio de origen de tercero asociado a la carga, creamos una provision
        :return:
        """
        for carga in self.carga_ids:
            if not carga.producto_servicio_ids:
                continue

            for servicio in carga.producto_servicio_ids:
                if servicio.product_type == 'terceros' and not servicio.provision_creada:
                    print("aca deberiamos crear la provision")
                    #Le pasamos.... el monto... el proveedor y el producto
                    if not servicio.partner_id:
                        raise Warning('No tiene producto')
                    if not servicio.currency_id:
                        raise Warning('No establecio la moneda')

                    self.crea_provision(proveedor=servicio.partner_id, producto=servicio.product_id, monto=servicio.valor_compra, moneda=servicio.currency_id, servicio=servicio)
                    servicio.provision_creada = True
        return

class rt_service_profit_carpeta(models.Model):
    _name = "rt.service.profit.carpeta"
    _description = "Profit de la Carpeta"

    rt_service_id = fields.Many2one(comodel_name='rt.service', string='Carpeta Relacionada')
    name = fields.Char(string='Concepto')
    debit = fields.Float(string='Debe', default=0.0)
    credit = fields.Float(string='Haber', default=0.0)