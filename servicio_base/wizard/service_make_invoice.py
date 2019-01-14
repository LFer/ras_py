# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.addons import decimal_precision as dp
import ipdb

class rt_service_advance_payment_inv(models.Model):
    _name = "rt.service.advance.payment.inv"
    _description = "Service Advance Payment Invoice"


    @api.multi
    def create_invoices(self):
        """ create invoices for the active service """
        context = self._context.copy()
        srv_ids = context.get('active_ids', [])
        act_window = self.env['ir.actions.act_window']
        wizard = self
        if wizard.advance_payment_method == 'lines':
            # open the list view of service product to invoice
            res = act_window.for_xml_id('servicio_base', 'action_rt_service_product_tree2')
            # context
            _pay_method = self.fields_get(allfields=['advance_payment_method'], attributes=['selection'])
            res['context'] = {
                'search_default_uninvoiced': 1,
                'search_default_filter_currency': 1 if _pay_method and _pay_method.get('advance_payment_method', {}).get('selection', [('all',)])[0][0] == 'lines' else 0
            }
            # domain
            if srv_ids:
                if not res.get('domain', False) or not isinstance(res.get('domain', False), (list,)):
                    res['domain'] = []
                res['domain'].append(('rt_service_id', 'in', srv_ids))
                res['domain'].append(('invoiced', '=', False))
                res['domain'].append(('is_invoiced', '=', True))
            return res




    rt_service_id = fields.Many2one(comodel_name='rt.service', string='Carpeta Relacionada')
    advance_payment_method = fields.Selection(selection=[('all', 'Facturar todos los Servicios'), ('percentage', 'Facturar un tramo'), ('lines', 'Algún servicio de la carpeta')], string='¿Qué desea facturar?', required=True, readonly=False)
    tramo_a_facturar = fields.Selection([('nactional', 'Nacional'), ('internacional', 'Internacional')], string='Tramo a Facturar')
    qtty = fields.Float('Quantity', digits=(16, 2), required=True)
    product_id = fields.Many2one('product.product', 'Advance Product', domain=[('type', '=', 'service')],help="""Select a product of type service which is called 'Advance Product'.You may have to create it and set it as a default value on this field.""")
    amount = fields.Float(string='Advance Amount', digits_compute= dp.get_precision('Account'), help="The amount to be invoiced in advance.")


