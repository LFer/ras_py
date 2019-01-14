# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    rt_service_product_id = fields.Many2one('rt.service.productos', string='Servicio Asociado')
    rt_service_id = fields.Many2one('rt.service', string='Carpeta Asociada')


