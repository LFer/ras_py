# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
import ipdb
from odoo.exceptions import UserError, RedirectWarning, Warning
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, tools, SUPERUSER_ID
AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]


class Camion(models.Model):
    _name = "camion"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'rating.mixin']
    _description = "Camiones para la vista Kanban"
    _order = "id DESC"

    name = fields.Char(string='Nombre')
    active = fields.Boolean(string='Activo', default=True)


class CargaCamion(models.Model):
    _name = "carga.camion"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'rating.mixin']
    _description = "Cargas"
    _order = "id DESC"

    def _default_camion_id(self):
        #team = self.env['crm.team'].sudo()._get_default_team_id(user_id=self.env.uid)
        return self.env['camion'].search([], limit=1).id
        #return self._stage_find(team_id=team.id, domain=[('fold', '=', False)]).id

    name = fields.Char(string='Referencia')
    camion_id = fields.Many2one('camion', string='Camion', default=lambda self: self._default_camion_id(), group_expand='_read_group_stage_ids')
    partner_id = fields.Many2one('res.partner', string='Customer')


    @api.model
    def _read_group_stage_ids(self, stages, domain, order):

        # search_domain = [('id', 'in', stages.ids)]
        # perform search
        search_vacio = [('active', '=', True)]
        stage_ids = stages._search(search_vacio, order=order, access_rights_uid=SUPERUSER_ID)
        #stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)


