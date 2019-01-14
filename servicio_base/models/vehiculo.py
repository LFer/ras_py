# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ExpirationType(models.Model):
    _name = 'expiration.type'
    _description = "Expiration type"

    name = fields.Char('Nombre', required=True)

class DocumentType(models.Model):
    _name = 'document.type'
    _description = "Tipo de Documento"

    name = fields.Char('Nombre', required=True)


class ExpirationTypeDate(models.Model):
    _name = 'expiration.type.date'
    _description = "Expiration type date"
    _rec_name = 'exp_type_id'

    exp_type_id = fields.Many2one(comodel_name='expiration.type', string='Tipo de expiración', required=True,
                                  ondelete="restrict")
    date = fields.Date('Fecha')
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', string='Vehículo',
                                 domain=[('vehicle_type', 'not in', ['hoist', 'container'])], ondelete="cascade")
    document_type_id = fields.Many2one(comodel_name='document.type', string='Tipo de Documento')
    attachment = fields.Many2many('ir.attachment')
    number = fields.Integer('Número')

class VehicleTypeSnub(models.Model):
    _name = 'vehicle.type.snub'
    _description = "Type of Snub"

    name = fields.Char('Nombre', required=True)


class VehicleAxis(models.Model):
    _name = 'vehicle.axis'
    _description = "Axis"

    name = fields.Char(string='Name', required=True)


class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _inherit = 'fleet.vehicle'
    _description = 'Information on a vehicle'

    rt_service_id = fields.Many2one(comodel_name='rt.service', string='Carpeta Relacionada')
    gps_type = fields.Selection([('nacional', 'Nacional'), ('inter', 'Internacional')], string='Tipo de Gps')
    license_plate = fields.Char('License Plate', required=False, help='License plate number of the vehicle (ie: plate number for a car)')
    vin_sn = fields.Char('Motor Number', help='Unique number written on the vehicle motor (VIN/SN number)')
    fletero_id = fields.Many2one('res.partner', 'Fletero', domain=[('freighter', '=', True)])
    driver_id = fields.Many2one('hr.employee', 'Chofer', help=u'Chofer del Vehículo')
    chassis_model = fields.Char(u'Número de Chasis')
    chassis_year = fields.Integer(u'Año de fabricación del chasis')
    vehicle_type = fields.Selection([('truck', 'Truck'),  # Camión
                                     ('semi_tow', 'Semi-Tow'),  # Semi remolque
                                     ('hoist', 'Permissive'),  # Montacarga
                                     ('container', 'Container'),  # Contenedor
                                     ('tractor', 'Tractor'),  # Tractor
                                     ('camioneta', 'Camioneta'),  # Camioneta
                                     ('nac_fleet', 'Fleteros nacional'),  # Fleteros nacional
                                     ('int_fleet', 'Fleteros internacional'),  # Fleteros internacional
                                     ('nac_vec_fleet', u'Vehículos fleteros nacional'),  # Vehículos fleteros nacional
                                     ('int_vec_fleet', u'Vehículos fleteros internacional'),  # Fleteros internacional
                                     ], u'Tipo de Vehículo', required=True, default='truck')
    crawl_capacity = fields.Float('Crawl capacity')
    imo = fields.Boolean('IMO')
    semi_tow_plate_id = fields.Many2one('fleet.vehicle', 'Semi-Tow licence plate', domain=[('vehicle_type', '=', 'semi_tow')])
    type_snub_id = fields.Many2one('vehicle.type.snub', 'Type of Snub')
    axis_qty_id = fields.Many2one('vehicle.axis', 'Quantity of axes')
    container_type = fields.Selection([('20', '20'),
                                       ('40', '40'),
                                       ('40 HC', '20 HC'),
                                       ('20 OT', '20 OT'),
                                       ('40 OT', '40 OT'),
                                       ('20 FR', '20 FR'),
                                       ('40 FR', '40 FR'),
                                       ('20 REEFER', '20 REEFER'),
                                       ('40 HC REEFER', '40 HC REEFER'),
                                       ('Other', 'Other')], string='Container Type')
    cont_ext_width = fields.Float('Width')
    cont_ext_height = fields.Float('Height')
    cont_ext_length = fields.Float('Length')
    cont_int_width = fields.Float('Width')
    cont_int_height = fields.Float('Height')
    cont_int_length = fields.Float('Length')
    owner_code = fields.Char('Owner code', size=4)
    serial_number = fields.Integer('Serial number')
    autocontrol_number = fields.Integer('Autocontrol number')
    size = fields.Float('Size')
    type = fields.Char('Type', size=2)
    tare = fields.Float('Tare')
    payload = fields.Float('Payload')
    cu_cup = fields.Float('Volume')
    is_ras_property = fields.Boolean('¿Propio?', default=True)
    expenses_ids = fields.One2many('default.expenses', 'vehicle_parent_id', string='Expenses')
    exp_type_date_ids = fields.One2many('expiration.type.date', 'vehicle_id', string='Expiration')
    libreta = fields.Binary(string='Libreta')
    fecha_vencimiento_libreta = fields.Date(string='Vencimiento')


    # def _vehicle_name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
    #     res = {}
    #     for record in self.browse(cr, uid, ids, context=context):
    #         res[record.id] = record.model_id.brand_id.name + '/' + record.model_id.modelname + (
    #             (' / ' + record.license_plate) if record.license_plate and record.license_plate != 'N/A' else "")
    #     return res

    @api.model
    def create(self,vals):
        if not vals.get('license_plate', False):
            vals['license_plate'] = 'N/A'
        return super(FleetVehicle, self).create(vals)

    @api.multi
    @api.onchange('is_ras_property')
    def onchange_ras_property(self):
        domain = { 'driver_id': [('driver','=',True)] }
        value = {}
        if self.is_ras_property:
            domain['driver_id'].append(('is_ras_property','=',True))
            value['driver_id'] = False
        return {'value': value, 'domain': domain}

    @api.multi
    @api.onchange('vehicle_type','driver_id','imo')
    def onchange_value_imo(self):
        return {}

    def return_action_to_open(self):
        context = self.env.context.copy() or {}
        for key in context.copy().keys():
            if key.startswith('default_') or key.startswith('search_default_') or key == 'tree_view_ref' or key == 'form_view_ref' or key == 'search_view_ref':
                context.pop(key)
        return super(FleetVehicle, self).return_action_to_open()

    @api.multi
    def act_show_log_cost(self):
        context = self.env.context.copy() or {}
        for key in context.copy().keys():
            if key.startswith('default_') or key.startswith('search_default_') or key == 'tree_view_ref' or key == 'form_view_ref' or key == 'search_view_ref':
                context.pop(key)
        return super(FleetVehicle, self).act_show_log_cost()
