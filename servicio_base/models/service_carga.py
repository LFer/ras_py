# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import ipdb
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models, _
from lxml import etree
_logger = logging.getLogger(__name__)

class rt_carga_tag(models.Model):
    _name = "carga.tags"
    _description = "Carga Tags"

    name = fields.Char(required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]

class rt_carga_stage(models.Model):
    _name = 'rt.carga.stage'
    _description = 'Carga Etapa'
    _order = 'sequence, id'

    def _get_default_project_ids(self):
        # default_project_id = self.env.context.get('default_project_id')
        # return [default_project_id] if default_project_id else None
        return None

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    # project_ids = fields.Many2many('project.project', 'project_task_type_rel', 'type_id', 'project_id', string='Projects',
    #     default=_get_default_project_ids)
    legend_priority = fields.Char(
        string='Starred Explanation', translate=True,
        help='Explanation text to help users using the star on tasks or issues in this stage.')
    legend_blocked = fields.Char(
        'Red Kanban Label', default=lambda s: _('Blocked'), translate=True, required=True,
        help='Override the default value displayed for the blocked state for kanban selection, when the task or issue is in that stage.')
    legend_done = fields.Char(
        'Green Kanban Label', default=lambda s: _('Ready for Next Stage'), translate=True, required=True,
        help='Override the default value displayed for the done state for kanban selection, when the task or issue is in that stage.')
    legend_normal = fields.Char(
        'Grey Kanban Label', default=lambda s: _('In Progress'), translate=True, required=True,
        help='Override the default value displayed for the normal state for kanban selection, when the task or issue is in that stage.')
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'project.task')],
        help="If set an email will be sent to the customer when the task or issue reaches this step.")
    fold = fields.Boolean(string='Folded in Kanban',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')
    rating_template_id = fields.Many2one(
        'mail.template',
        string='Rating Email Template',
        domain=[('model', '=', 'project.task')],
        help="If set and if the project's rating configuration is 'Rating when changing stage', then an email will be sent to the customer when the task reaches this step.")
    auto_validation_kanban_state = fields.Boolean('Automatic kanban status', default=False,
        help="Automatically modify the kanban state when the customer replies to the feedback for this stage.\n"
            " * A good feedback from the customer will update the kanban state to 'ready for the new stage' (green bullet).\n"
            " * A medium or a bad feedback will set the kanban state to 'blocked' (red bullet).\n")

class rt_service_profit_carga(models.Model):
    _name = "rt.service.profit.carga"
    _description = "Profit de la Carga"

    rt_carga_id = fields.Many2one(comodel_name='rt.service.carga', string='Carga Relacioada')
    name = fields.Char(string='Concepto')
    debit = fields.Float(string='Debe', default=0.0)
    credit = fields.Float(string='Haber', default=0.0)



class rt_service_carga(models.Model):
    _name = "rt.service.carga"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'rating.mixin']
    _description = "Cargas"
    _order = "id DESC"

    @api.model
    def create(self, vals):
        context = self._context
        if context is None:
            context = {}
        if not vals.get('name', False):
            if 'operation_type' in vals and vals['operation_type'] == 'national':
                vals['name'] = self.env['ir.sequence'].next_by_code('rt.carga.nacional') or '/'
            if 'operation_type' in vals and vals['operation_type'] == 'international':
                vals['name'] = self.env['ir.sequence'].next_by_code('rt.carga.internacional') or '/'
        return super(rt_service_carga, self).create(vals)





    @api.one
    @api.depends('profit_carga')
    def compute_carga_profit(self):
        debit = sum(x.debit for x in self.profit_carga_ids)
        credit = sum(x.credit for x in self.profit_carga_ids)
        balance = credit - debit
        self.profit_carga = balance

    def _compute_seller_commission(self):
        return

    @api.one
    @api.depends('seller_commission_percent')
    def _compute_commission_to_pay(self):
        # self.commission_to_pay = 0.0
        # if self.rt_carga_id:
        #     # Important! Commission to pay is expressed in service currency, not in service-product currency
        #     self.commission_to_pay = (self.rt_carga_id.rt_service_id.travel_commission or 0.0) * (self.seller_commission_percent or 0.0) / 100.0
        return





    operation_type = fields.Selection(related='rt_service_id.operation_type', string='Tipo de Servicio', readonly=False, store=True)
    regimen = fields.Selection(related='rt_service_id.regimen', string='Regimen', store=True)
    pricelist_id = fields.Many2one('product.pricelist.item', string='Tarifa')
    commission_to_pay = fields.Float('Comisión a pagar', compute='_compute_commission_to_pay', readonly=True, store=True, digits_compute=dp.get_precision('Account'),help="Comisión a pagar expresada en la moneda del Servicio.")
    is_seller_commission = fields.Boolean(string='Comisión al vendedor')
    partner_seller_id = fields.Many2one(comodel_name='res.partner', string='Vendedor', domain=[('seller', '=', True)])
    seller_commission_percent = fields.Float('Porcentaje de Comisión a Vendedores',compute='_compute_seller_commission', readonly=True, store=True)
    seller_commission_fixed_by_user = fields.Float('Commisión fijada por el usuario', size=64)
    payment_date = fields.Date(string='Fecha de Pago', copy=False, readonly=True)
    active = fields.Boolean(default=True)
    xls_name = fields.Char(string='File Name', size=128)
    gen_crt_report = fields.Boolean(string='Seleccionar')
    producto_servicio_ids = fields.One2many('rt.service.productos', 'rt_carga_id', string='Cargas')
    profit_carga_ids = fields.One2many('rt.service.profit.carga', 'rt_carga_id', string='Profit Carga', comppute='get_profit_carga')
    rt_service_id = fields.Many2one(comodel_name='rt.service', string='Carpeta Relacionada')
    dangers_loads = fields.Boolean(string='Carga Peligrosa')
    name = fields.Char(string='Referencia')
    load_type = fields.Selection([('bulk','Bulk'),('contenedor','Contenedor'),('liquido_granel',u'Granel Líquido'),('solido_granel',u'Granel Solido')], string='Tipo de Carga')
    load_presentation = fields.Selection([('pallet', 'Pallet'), ('paquete','Paquete'), ('otros', 'Otros')], string=u'Presentación')
    pallet_type = fields.Selection([('euro', 'Europeo'), ('merco','Mercosur')], string=u'Tipo Pallet')

    container_type = fields.Many2one(comodel_name='fleet.vehicle', string='Tipo de Contenedor', domain=[('vehicle_type','=', 'container')])
    # container_size = fields.Float('Size', readonly=True, compute="_get_container_size")
    #Cuando es Contenedor
    dua_linea = fields.Char(string='DUA')
    container_size = fields.Float(u'Tamaño')
    bookingk = fields.Char('Booking', size=32)
    tack = fields.Char('Virada', size=32)
    cut_off_doc = fields.Datetime('Cut off Documentario')
    cut_off_operative = fields.Datetime('Cut off Operativo')
    cut_off_documentario = fields.Datetime('Cut off Documentario')
    container_number = fields.Char(string=u'Número de contenedor', size=32)
    seal_number = fields.Char(string='Número de precinto', size=32)
    payload = fields.Float(string='Payload')
    tare = fields.Float('Tara')
    terminal_retreat = fields.Many2one(comodel_name='res.partner.address.ext',  string='Terminal de Retiro', ondelete='restrict')
    terminal_retreat_deposit = fields.Many2one(comodel_name='res.partner.address.ext', string='Depósito de Retiro',ondelete='restrict')
    terminal_return = fields.Many2one(comodel_name='res.partner.address.ext',  string=u'Terminal de Devolución', ondelete='restrict')

    #Cuando es Bulk
    volume = fields.Float(string='Volumen')
    net_kg = fields.Float(string='Kg Neto')
    raw_kg = fields.Float(string='Kg Bruto')
    package = fields.Float(string='Bultos')
    profit_carga = fields.Float(string='Profit Carga', compute='compute_carga_profit')



    xls_file = fields.Binary(string='XLS File')
    ras_is_carrier = fields.Boolean('Ras es transportista')
    imo = fields.Boolean('IMO')
    crt = fields.Boolean('CRT')
    container_qty = fields.Integer('Cantidad de contenedores')
    #Datos para el CRT
    remitente_id = fields.Many2one(comodel_name='asociados.carpeta', string='Remitente', domain="[('type', '=','remitente')]")
    consigantario_id = fields.Many2one(comodel_name='asociados.carpeta', string='Consignatario', domain="[('type', '=','consignatario')]")
    destinatario_id = fields.Many2one(comodel_name='asociados.carpeta', string='Destino', domain="[('type', '=','destino')]")
    notificar_id = fields.Many2one(comodel_name='asociados.carpeta', string='Avisar a ',domain="[('type', '=','notificar')]")
    country_id = fields.Many2one(comodel_name='res.country', string='País')
    crt_number = fields.Char('Numero CRT')
    kilaje_carga = fields.Float(string='Kilage de la Carga')
    volumen_est = fields.Char(string='Volumen Estimado')
    valor_mercaderia = fields.Float(string='Valor de la Mercaderia')
    valor_mercaderia_text = fields.Char(string='Valor de la mercaderia en texto')
    valor_mercaderia_currency_id = fields.Many2one(string='Moneda', comodel_name='res.currency')
    description = fields.Text(string='Descripción')
    origen_destino = fields.Char(string='Origen-Destino')
    importe = fields.Float(string='Valor de Venta', store=True)
    costo_estimado = fields.Float(string='Costo Referencia')
    importe_currency_id = fields.Many2one(comodel_name="res.currency", string="Moneda", index=True, store=True)
    costo_estimado_currency_id = fields.Many2one(comodel_name="res.currency", string="Moneda", index=True, store=True)
    make_page_invisible = fields.Boolean(help='Este booleano es para hacer invisible la pagina si no se cargo regimen, cliente a facturar')
    make_presentacion_invisible = fields.Boolean(help='Esto va hacer el campo presentacion invisible')
    make_dua_invisible_or_required = fields.Boolean(help='Este campo me va ayudar hacer el dua de las cargas invisible o visible y requerido')
    make_terminal_devolucion_invisible = fields.Boolean(help='Esto hace el campo terminal de devolucion invisible')
    carga_qty = fields.Integer(string='Cantidad')
    carga_m3 = fields.Float(string='m3')
    libre_devolucion = fields.Datetime(string='Libre de Devolución')
    preasignado = fields.Boolean(string='Preasignado')
    partner_id = fields.Many2one('res.partner',string='Customer')
    comentarios = fields.Text(string='Referencia')
    partner_invoice_id = fields.Many2one(comodel_name='res.partner', string='Cliente a facturar', domain=[('customer', '=', True)])
    peso_total = fields.Float(string='Peso Total')




    @api.onchange('partner_invoice_id', 'name')
    def _onchange_partner_id(self):
        domain = {}
        warning = {}
        res = {}
        tipo_servicio = ''


        address_obj = self.env['res.partner.address.ext']
        partner_obj = self.env['res.partner']
        if self.rt_service_id:
            for line in self.rt_service_id.rt_servicios_ids:
                if line.service_type_id.name == 'FCL':

                    tipo_servicio = line.service_type_id.name
                    break

        if tipo_servicio == 'FCL':
            partner_playa = partner_obj.search([('playa', '=', True)])
            if len(partner_playa) >= 2:
                addresses = address_obj.search([('partner_id', 'in', partner_playa.ids), ('address_type', '=', 'beach')])
            else:
                addresses = address_obj.search([('partner_id', '=', partner_playa.id), ('address_type', '=', 'beach')])

            if not addresses:
                warning = {
                    'title': _("Alerta para %s") % self.partner_invoice_id.name,
                    'message': "No se encontró Lugar para el cliente"
                }

            domain = {'terminal_retreat': [('id', 'in', addresses.ids)], 'terminal_return': [('id', 'in', addresses.ids)]}

            if warning:
                res['warning'] = warning
            if domain:
                res['domain'] = domain
            return res

        if self.partner_invoice_id:
            partner_id = self.partner_invoice_id.id
            addresses = address_obj.search([('partner_id', '=', partner_id)])

            if not addresses:
                warning = {
                    'title': _("Alerta para %s") % self.partner_invoice_id.name,
                    'message': "No se encontró Lugar para el cliente"
                }

            domain = {'terminal_retreat': [('id', 'in', addresses.ids)], 'terminal_return': [('id', 'in', addresses.ids)]}

        if warning:
            res['warning'] = warning
        if domain:
            res['domain'] = domain
        return res


    @api.multi
    @api.onchange('load_type')
    def get_container_size(self):
        pricelist_item_obj = self.env['product.pricelist.item']
        carpeta = self.rt_service_id
        partner = carpeta.partner_invoice_id.id
        pricelist_items = pricelist_item_obj.search([('partner_id', '=', partner), ('load_type', '=', self.load_type)])
        if pricelist_items:
            self.pricelist_id = pricelist_items.id
            if len(pricelist_items) >= 2:
                #Por ahora me quedo con el primer elemento
                self.importe = pricelist_items[0].sale_price
            else:
                self.importe = pricelist_items.sale_price
            self.partner_seller_id = carpeta.partner_invoice_id.user_id.partner_id.id
            self.importe_currency_id = carpeta.currency_id.id
            self.make_dua_invisible_or_required = carpeta.make_dua_invisible_or_required
        for rec in self:
            if rec.container_type:
                rec.container_size = rec.container_type.size

    def _compute_attachment_ids(self):
        # for task in self:
        #     attachment_ids = self.env['ir.attachment'].search([('res_id', '=', task.id), ('res_model', '=', 'rt.service.carga')]).ids
        #     message_attachment_ids = task.mapped('message_ids.attachment_ids').ids  # from mail_thread
        #     task.attachment_ids = list(set(attachment_ids) - set(message_attachment_ids))
        return


rt_service_carga()