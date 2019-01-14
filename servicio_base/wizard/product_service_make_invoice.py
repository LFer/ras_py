# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import ipdb
from odoo.tools import float_is_zero, float_compare

class MakeInvoice(models.TransientModel):
    _name = 'rt.service.product.make.invoice'
    _description = 'Create Mass Invoice (repair)'

    group = fields.Boolean('Group by partner invoice address')



    @api.multi
    def make_invoices(self):
        inv_obj = self.env['account.invoice']
        if not self._context.get('active_ids'):
            return {'type': 'ir.actions.act_window_close'}
        product_service = self.env['rt.service.productos'].browse(self._context.get('active_ids')[0])
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        operation_national = ['transit_nat', 'impo_nat', 'expo_nat', 'interno_plaza_nat', 'interno_fiscal_nat']
        operation_taxes = {'exento': False, 'asimilado': False, 'gravado': False}

        lineas = []
        for line in product_service:
            if line.operation_type == 'national':
                if line.regimen == 'impo_nat':
                    taxes = operation_taxes['gravado']
                    line_dict = {}
                    line_dict['name'] = line.name
                    line_dict['account_id'] = line.product_id.categ_id.property_account_income_categ_id.id
                    line_dict['price_unit'] = line.importe
                    line_dict['uom_id'] = line.product_id.uom_id.id
                    line_dict['product_id'] = line.product_id.id
                    line_dict['invoice_line_tax_ids'] = [(6, 0, line.product_id.taxes_id.ids)]
                    lineas.append((0, 0, line_dict))
                    #Facturado
                    line.invoiced = True

                invoice = inv_obj.create({
                    'name': product_service.rt_service_id.partner_invoice_id.name or '',
                    'origin': product_service.name,
                    'type': 'out_invoice',
                    'account_id': product_service.rt_service_id.partner_invoice_id.property_account_receivable_id.id,
                    'partner_id': product_service.rt_service_id.partner_invoice_id.id,
                    'journal_id': journal_id,
                    'currency_id': product_service.currency_id.id,
                    'fiscal_position_id': product_service.rt_service_id.partner_invoice_id.property_account_position_id.id,
                    'company_id': product_service.rt_service_id.company_id.id,
                    'user_id': product_service.rt_service_id.user_id and product_service.rt_service_id.user_id.id,
                    'rt_service_product_id': product_service.id,
                    'rt_service_id': product_service.rt_service_id.id,
                    'invoice_line_ids': lineas
                })

                line.invoices_ids = invoice
                line.rt_service_id.invoices_ids = invoice



        if self._context['open_invoices']:
            return {
                'domain': [('id', 'in', invoice.ids)],
                'name': 'Invoices',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'view_id': False,
                'views': [(self.env.ref('account.invoice_tree').id, 'tree'), (self.env.ref('account.invoice_form').id, 'form')],
                'context': "{'type':'out_invoice'}",
                'type': 'ir.actions.act_window'
            }
        else:
            return {'type': 'ir.actions.act_window_close'}
