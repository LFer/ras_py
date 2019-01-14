# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class rt_service_line(models.Model):
    _name = "rt.service.line"

    rt_service_id = fields.Many2one(comodel_name='rt.service', string='Carpeta Relacionada')
    service_type_id = fields.Many2one(comodel_name='rt.service.type', string=u'Tipo de Servicio')
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', string='Modelo',domain=[('vehicle_type', '=', 'container')], ondelete="cascade")
    qty = fields.Float(string='Cantidad')

class rt_service_type(models.Model):
    _name = "rt.service.type"
    _description = "Tipo de Servicio"

    name = fields.Char(string='Tipo de Servicio')



