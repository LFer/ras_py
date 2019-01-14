# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.osv import expression
import ipdb
from odoo.osv.expression import get_unaccent_wrapper
import re

class ResCountryCity(models.Model):
    _name = 'res.country.city'

    name = fields.Char(string='Nombre')
    country_id = fields.Many2one('res.country', string='Pais')
    code = fields.Char(related='country_id.codigo_pais')

class ResPartnerAddressExt(models.Model):
    _name = 'res.partner.address.ext'

    name = fields.Char('Nombre Corto')
    street = fields.Char('Calle')
    street2 = fields.Char('Esquina')
    zip = fields.Char('C.P.', size=24, change_default=True)
    city_id = fields.Many2one('res.country.city', 'Ciudad')
    state_id = fields.Many2one("res.country.state", 'Estado', ondelete='restrict')
    country_id = fields.Many2one('res.country', 'País', ondelete='restrict')
    partner_id = fields.Many2one('res.partner', 'Empresa', ondelete='cascade')
    address_type = fields.Selection([
        ('load', 'Carga Suelta'),
        ('beach', 'Playa de Contenedores'),
        ('invoice', u'Facturación'),
        ('tienda', u'Tienda'),
    ], 'Tipo de Depósito')
    opening = fields.Float('Apertura')
    closing = fields.Float('Cierre')
    rest = fields.Integer('Descanso')
    place_id = fields.Many2one('stock.warehouse', 'Depósito', required=False)
    deposit_number = fields.Char(string='Número de Depósito')
    aduana_id = fields.Many2one('fronteras', string='Clave Aduanera')


class ResPartnerExpirationTypeDate(models.Model):
    _name = 'res.partner.expiration.type.date'
    _description = "Partner Expiration type date"
    _rec_name = 'exp_type_id'

    exp_type_id = fields.Many2one('res.partner.expiration.type', u'Tipo de expiración', required=True, ondelete="restrict")
    date = fields.Date('Date')
    partner_id = fields.Many2one('res.partner', 'Empresa', domain=[('driver', '=', True)], ondelete="cascade")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    address_ext_ids = fields.One2many('res.partner.address.ext', 'partner_id', u'Dirección')
    expenses_ids = fields.One2many('default.expenses', 'partner_parent_id', string='Gastos')
    exp_type_date_ids = fields.One2many('res.partner.expiration.type.date', 'partner_id', string=u'Expiración')
    social_reason = fields.Char(u'Razón Social', size=254)
    dispatcher = fields.Boolean('Despachante')
    freighter = fields.Boolean('Fletero')
    permissive = fields.Boolean('Permisado')
    dangers_loads = fields.Boolean('Carga Peligrosa')
    native_lic_number = fields.Integer(u'Número de Permiso Originario', size=20)
    native_lic_date = fields.Date('Fecha de Permiso Originario')
    comp_lic_number = fields.Integer(u'Número de Permiso Complementario', size=20)
    comp_lic_date = fields.Date('Fecha de Permiso Complementario')
    policy_number = fields.Integer(u'Número de Póliza de Seguros')
    ministries = fields.Boolean('MTOP')
    driver = fields.Boolean('Chofer')
    imo = fields.Boolean('IMO')
    gen_of_message = fields.Boolean('Generador de Mensaje Simplificado')
    user_zf = fields.Boolean('Usuario ZF')
    remittent = fields.Boolean('Remitente')
    receiver = fields.Boolean('Destinatario')
    supplier_peons = fields.Boolean('Proveedor de Peones')
    supplier_hoist = fields.Boolean('Proveedor Montacargas')
    consignee = fields.Boolean('Consignatario')
    carrier = fields.Boolean('Porteador')
    where_paper = fields.Boolean('Donde quedan los papeles')
    load_agent = fields.Boolean('Agente de Carga')
    seller = fields.Boolean('Vendedor')
    deposito = fields.Boolean(u'Depósito')
    partner_seller_id = fields.Many2one('res.partner', 'Vendedor', domain=[('seller', '=', True)])
    documentacion = fields.Boolean(string=u'Documentación')
    is_ras_property = fields.Boolean('Es Propiedad de Ras Transport')
    playa = fields.Boolean(string='Playa de Contenedores')

    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     if 'social_reason' in self._fields:
    #         args = expression.OR([args or [], [('social_reason', operator, name)]])
    #     return super(ResPartner, self)._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     if 'social_reason' in self._fields:
    #         self = self.sudo(name_get_uid or self.env.uid)
    #         if args is None:
    #             args = []
    #
    #         if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
    #             self.check_access_rights('read')
    #             where_query = self._where_calc(args)
    #             self._apply_ir_rules(where_query, 'read')
    #             from_clause, where_clause, where_clause_params = where_query.get_sql()
    #             where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '
    #
    #             # search on the name of the contacts and of its company
    #             search_name = name
    #             if operator in ('ilike', 'like'):
    #                 search_name = '%%%s%%' % name
    #             if operator in ('=ilike', '=like'):
    #                 operator = operator[1:]
    #
    #             unaccent = get_unaccent_wrapper(self.env.cr)
    #
    #             query = """SELECT id
    #                          FROM res_partner
    #                       {where} ({email} {operator} {percent}
    #                            OR {display_name} {operator} {percent}
    #                            OR {reference} {operator} {percent}
    #                            OR {vat} {operator} {percent})
    #                            -- don't panic, trust postgres bitmap
    #                      ORDER BY {display_name} {operator} {percent} desc,
    #                               {display_name}
    #                     """.format(where=where_str,
    #                                operator=operator,
    #                                email=unaccent('email'),
    #                                display_name=unaccent('display_name'),
    #                                reference=unaccent('social_reason'),
    #                                percent=unaccent('%s'),
    #                                vat=unaccent('vat'),)
    #
    #             where_clause_params += [search_name]*3  # for email / display_name, reference
    #             where_clause_params += [re.sub('[^a-zA-Z0-9]+', '', search_name)]  # for vat
    #             where_clause_params += [search_name]  # for order by
    #             if limit:
    #                 query += ' limit %s'
    #                 where_clause_params.append(limit)
    #             self.env.cr.execute(query, where_clause_params)
    #             partner_ids = [row[0] for row in self.env.cr.fetchall()]
    #
    #             if partner_ids:
    #                 return self.browse(partner_ids).name_get()
    #             else:
    #                 return []
    #     return super(ResPartner, self)._name_search(name, args, operator=operator, limit=limit, name_get_uid=name_get_uid)


    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if 'social_reason' in self._fields:
            args = args or []
            recs = self.browse()
            recs = self.search(['|', '|', '|', ('name', operator, name), ('social_reason', operator, name), ('vat', operator, name), ('ref', operator, name)] + args, limit=limit)
        return recs.name_get()