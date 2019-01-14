# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields

class CatalogoTipoBulto(models.Model):
    _name = 'catalogo.tipo.bulto'
    _description = 'Catálogo tipo de Bultos'

    name = fields.Char(string='Equivalencia')
    desc = fields.Char(string='Descripción')
    tipo_bulto = fields.Char(string='Tipo de Bulto')
    info = fields.Char(string='Observaciones')
