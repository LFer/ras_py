# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
import ipdb

_logger = logging.getLogger(__name__)


class rt_service_productos(models.Model):
    _inherit = "rt.service.productos"

    obs = fields.Text(string='Observaciones')
    calendar_cantidad = fields.Char()
    calendar_size = fields.Char()
    calendar_ref = fields.Char()
    calendar_matricula = fields.Char()
    calendar_dua = fields.Char()
    calendar_partner_chofer_id = fields.Char()
    calendar_partner_chofer_fletero = fields.Char()
    calendar_partner_id = fields.Char()
    calendar_container_number = fields.Char()
    calendar_matricula_semi = fields.Char()
    calendar_matricula_dos = fields.Char()
    html_field = fields.Html(string='Info', readonly=True)

    @api.multi
    @api.depends('calendar_html')
    def get_info_from_nodes(self):

        saldo = 20
        dua = ''
        dua_linea = ''
        table = ''
        table += '<table style="width:100%;">'
        table += '<thead style="border: thin solid gray;">'
        table += '<tr style="border: thin solid gray;">'
        table += '<th style="border: thin solid gray; text-align: center">Nro Contenedor</th>'
        table += '<th style="border: thin solid gray; text-align: center">DUA</th>'
        table += '<th style="border: thin solid gray; text-align: center">Matricula</th>'
        table += '<th style="border: thin solid gray; text-align: center">Matricula dos</th>'
        table += '<th style="border: thin solid gray; text-align: center">Chofer</th>'
        table += '<th style="border: thin solid gray; text-align: center">Fletero</th>'
        table += '</tr style="border: thin solid gray;">'
        table += '</thead>'
        table += '<tbody>'
        dict =  {'numero_contenedor': '',
              'dua': '',
              'matricula': '',
              'matricula_dos': '',
              'vehiculo': '',
              'chofer': '',
              'fletero': '',

              }

        for line in self.rt_carpeta_id.carga_ids:
            if self.rt_carpeta_id.dua_type == 'cabezal':
                dua = self.rt_carpeta_id.dua_cabezal

            table += '<tr style="border: thin solid gray;">'
            table += '<td style="border: thin solid gray;text-align:center;"````>%(dep)s</td>' % {'dep': line.container_number} #Numero de Contenedor
            nro_contenedor = line.container_number
            table += '<td style="border: thin solid gray;text-align:center;"````>%(dep)s</td>' % {'dep': dua}  #DUA

        for srv in self.env['rt.service.productos'].search([('rt_service_id', '=', self.rt_carpeta_id.id)]):
            # table += '<td style="border: thin solid gray;text-align:center;"````>0.0</td>'
            # table += '<td style="border: thin solid gray;text-align:center;"````>0.0</td>'
            if srv.product_type == 'propio':
                table += '<td style="border: thin solid gray;text-align:center;"````>%(dep)s</td>' % {'dep': srv.vehicle_id.license_plate}  # MATRICULA
                table += '<td style="border: thin solid gray;text-align:center;"````>%(dep)s</td>' % {'dep': srv.matricula_dos}  # MATRICULA 2
                table += '<td style="border: thin solid gray;text-align:center;"````>%(dep)s</td>' % {'dep': srv.driver_id.name}  # Chofer
                table += '<td style="border: thin solid gray;text-align:center;"````>N/A</td>'
            if srv.product_type == 'terceros':
                table += '<td style="border: thin solid gray;text-align:center;"````>%(dep)s</td>' % {'dep': nro_contenedor}  # nro_contenedor
                table += '<td style="border: thin solid gray;text-align:center;"````>%(dep)s</td>' % {'dep': dua}  # dua
                table += '<td style="border: thin solid gray;text-align:center;"````>N/A</td>'
                table += '<td style="border: thin solid gray;text-align:center;"````>N/A</td>'
                table += '<td style="border: thin solid gray;text-align:center;"````>N/A</td>'
                table += '<td style="border: thin solid gray;text-align:center;"````>%(dep)s</td>' % {'dep': srv.fletero_id.name}  # Fletero
            table += '</tr>'
            pass

        table += '</tbody>'
        table += '</table>'

        self.html_field = table


    # @api.multi
    # @api.onchange('rt_carga_id', 'rt_carpeta_id')
    # def onchange_fields(self):
    #     print("entro---")
    #     for record in self:
    #         record.calendar_matricula = record.vehicle_id.license_plate
    #         record.calendar_partner_id = record.partner_id.name
    #         if record.rt_carga_id:
    #             record.calendar_cantidad = record.rt_carga_id.container_qty
    #             record.calendar_size = record.rt_carga_id.container_size
    #             record.calendar_ref = record.rt_carga_id.name
    #             record.calendar_dua = record.rt_carga_id.dua_linea
    #
    #         if record.rt_carpeta_id:
    #             record.calendar_partner_id = record.rt_carpeta_id.partner_id.name