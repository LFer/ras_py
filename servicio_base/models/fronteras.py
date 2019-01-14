# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields

class Country(models.Model):
    _inherit = 'res.country'

    codigo_pais = fields.Char(string='Código DNA')


class Fronteras(models.Model):
    _name = "fronteras"

    name = fields.Char(string='Nombre')
    codigo = fields.Char(string='Código')
    codigo_dna = fields.Char(string='Código DNA')
    image = fields.Binary("Image", attachment=True, help="This field holds the image used as avatar for this contact, limited to 1024x1024px", )
    country_id = fields.Many2one('res.country', string='País', ondelete='restrict')
    codigo_pais = fields.Char(string='Código País', related="country_id.codigo_pais")

