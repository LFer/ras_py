# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Servicio Base',
    'version': '1.1',
    'category': u'Logística',
    'sequence': 75,
    'summary': u'Módulo base',
    'description': """
Módulo base para operativa
==========================

Esta aplicación le permite trabajar con operativas de logistica


Extiende:
---------
* Empleados y Jerarquias
* Clientes y Proveedores
    """,
    'website': 'https://www.odoo.com/page/employees',
    'images': [
    ],
    'depends': [
        'rating',
        'portal',
        'web',
        'base',
        'hr',
        #'account',
        'payment',
        'mail',
        'stock',
        'fleet',
        'mail',
    ],
    'data': [
        'views/service_menu.xml',
        'wizard/create_invoice_wizard.xml',
        'data/service_sequence.xml',
        'views/res_partner_view.xml',
        #'views/carga_view.xml',
        'views/account_invoice_view.xml',
        #'views/product_view.xml',
        'views/service_base_view.xml',
        'views/vehiculo_view.xml',
        'views/asociados_carpeta_view.xml',
        'views/tarifario_view.xml',
        'views/search_views.xml',
        'security/servicio_security.xml',
        'security/ir.model.access.csv',
        'views/product_service_view.xml',
        'views/service_template_view.xml',
        'views/service_calendar_menu_view.xml',
        'views/fronteras_view.xml',
        'views/depositos_view.xml',
        'views/catalogos_bultos.xml',

    ],
    'external_dependencies':{
        'python':['xmltodict','qrcode','ipdb']
    },    
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
