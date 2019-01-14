# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, RedirectWarning, Warning
import ipdb
_logger = logging.getLogger(__name__)


class ExpenseProvision(models.Model):
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _name = 'expense.provision'
    _description = 'Expenses Provisions'

    @api.one
    @api.depends('expense_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount_untaxed = sum(line.price_subtotal for line in self.expense_line_ids)
        self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax


    @api.model
    def _default_journal(self):
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [('company_id', '=', company_id),('type','=','purchase')]
        journal = self.env['account.journal'].search(domain, limit=1)
        return journal

    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        return journal.currency_id or journal.company_id.currency_id or self.env.user.company_id.currency_id



    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user, copy=False)
    name = fields.Char(string='Reference/Description', index=True, readonly=True, states={'draft': [('readonly', False)]}, copy=False, help='The name that will be used on account move lines')
    origin = fields.Char(string='Source Document', help="Reference of the document that produced this invoice.", readonly=True, states={'draft': [('readonly', False)]})
    number = fields.Char(related='move_id.name', store=True, readonly=True, copy=False)
    move_name = fields.Char(string='Journal Entry Name', readonly=False,
                            default=False, copy=False)
    state = fields.Selection([
        ('draft','Draft'),
        ('open', 'Confirmed'),
        ('invoiced', 'Invoice Created'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'In Payment' status is used when payments have been registered for the entirety of the invoice in a journal configured to post entries at bank reconciliation only, and some of them haven't been reconciled with a bank statement line yet.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")
    date_invoice = fields.Date(string='Invoice Date', readonly=True, states={'draft': [('readonly', False)]}, index=True, help="Keep empty to use the current date", copy=False)
    account_id = fields.Many2one('account.account', string='Account',readonly=True, states={'draft': [('readonly', False)]}, domain=[('deprecated', '=', False)],
                                 help="The partner account used for this invoice.")
    journal_id = fields.Many2one('account.journal', string='Journal',required=True, readonly=True, states={'draft': [('readonly', False)]},default=_default_journal)
    company_id = fields.Many2one('res.company', string='Company', change_default=True,required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
    date_due = fields.Date(string='Due Date',
                           readonly=True, states={'draft': [('readonly', False)]}, index=True, copy=False,
                           help="If you use payment terms, the due date will be computed automatically at the generation "
                                "of accounting entries. The Payment terms may compute several due dates, for example 50% "
                                "now and 50% in one month, but if you want to force a due date, make sure that the payment "
                                "term is not set on the invoice. If you keep the Payment terms and the due date empty, it "
                                "means direct payment.")
    partner_id = fields.Many2one('res.partner', string='Partner', change_default=True, readonly=True, states={'draft': [('readonly', False)]},track_visibility='always', help="You can find a contact by its Name, TIN, Email or Internal Reference.")
    expense_line_ids = fields.One2many('expense.provision.line', 'expense_provision_id', string='Exprense Provisions Line', readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    tax_line_ids = fields.One2many('expense.provision.tax', 'expense_provision_id', string='Tax Lines', readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, index=True, ondelete='restrict', copy=False, help="Link to the automatically generated Journal Items.")
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_compute_amount', track_visibility='always')
    amount_tax = fields.Monetary(string='Tax', store=True, readonly=True, compute='_compute_amount')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=_default_currency, track_visibility='always')
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True)
    comment = fields.Text('Additional Information', readonly=True, states={'draft': [('readonly', False)]})
    reference = fields.Char(string='Payment Ref.', copy=False, readonly=True, states={'draft': [('readonly', False)]}, help='The payment communication that will be automatically populated once the invoice validation. You can also write a free communication.')
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', oldname='fiscal_position', readonly=True, states={'draft': [('readonly', False)]})
    invoice_id = fields.Many2one('account.invoice', string='Invoice Reference', ondelete='cascade', index=True, readonly=True, copy=False)
    rt_service_product_id = fields.Many2one('rt.service.productos', string='Servicio Asociado')

    @api.model
    def line_get_convert(self, line, part):
        return self.env['product.product']._convert_prepared_anglosaxon_line(line, part)

    @api.model
    def invoice_line_move_line_get(self):
        res = []
        for line in self.expense_line_ids:
            if not line.account_id:
                continue
            if line.quantity==0:
                continue
            tax_ids = []
            for tax in line.provision_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))

            move_line_dict = {
                'type': 'src',
                'name': line.name,
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'price': line.price_subtotal,
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'tax_ids': tax_ids,
                'expense_provision_id': self.id,
            }
            res.append(move_line_dict)
        return res

    @api.model
    def tax_line_move_line_get(self):
        res = []
        # keep track of taxes already processed
        done_taxes = []
        # loop the invoice.tax.line in reversal sequence
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.amount_total:
                tax = tax_line.tax_id
                if tax.amount_type == "group":
                    for child_tax in tax.children_tax_ids:
                        done_taxes.append(child_tax.id)
                res.append({
                    'invoice_tax_line_id': tax_line.id,
                    'tax_line_id': tax_line.tax_id.id,
                    'type': 'tax',
                    'name': tax_line.name,
                    'price_unit': tax_line.amount_total,
                    'quantity': 1,
                    'price': tax_line.amount_total,
                    'account_id': tax_line.account_id.id,
                    'account_analytic_id': tax_line.account_analytic_id.id,
                    'expense_provision_id': self.id,
                    'tax_ids': [(6, 0, list(done_taxes))] if tax_line.tax_id.include_base_amount else []
                })
                done_taxes.append(tax.id)
        return res

    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        total = 0
        total_currency = 0
        type = 'in_invoice'
        for line in invoice_move_lines:
            if self.currency_id != company_currency:
                currency = self.currency_id
                date = self._get_currency_rate_date() or fields.Date.context_today(self)
                if not (line.get('currency_id') and line.get('amount_currency')):
                    line['currency_id'] = currency.id
                    line['amount_currency'] = currency.round(line['price'])
                    line['price'] = currency._convert(line['price'], company_currency, self.company_id, date)
            else:
                line['currency_id'] = False
                line['amount_currency'] = False
                line['price'] = self.currency_id.round(line['price'])
            if type in ('out_invoice', 'in_refund'):
                total += line['price']
                total_currency += line['amount_currency'] or line['price']
                line['price'] = - line['price']
            else:
                total -= line['price']
                total_currency -= line['amount_currency'] or line['price']
        return total, total_currency, invoice_move_lines


    def group_lines(self, iml, line):
        """Merge account move lines (and hence analytic lines) if invoice line hashcodes are equals"""
        if self.journal_id.group_invoice_lines:
            line2 = {}
            for x, y, l in line:
                tmp = self.inv_line_characteristic_hashcode(l)
                if tmp in line2:
                    am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                    line2[tmp]['debit'] = (am > 0) and am or 0.0
                    line2[tmp]['credit'] = (am < 0) and -am or 0.0
                    line2[tmp]['amount_currency'] += l['amount_currency']
                    line2[tmp]['analytic_line_ids'] += l['analytic_line_ids']
                    qty = l.get('quantity')
                    if qty:
                        line2[tmp]['quantity'] = line2[tmp].get('quantity', 0.0) + qty
                else:
                    line2[tmp] = l
            line = []
            for key, val in line2.items():
                line.append((0, 0, val))
        return line

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ finalize_invoice_move_lines(move_lines) -> move_lines

            Hook method to be overridden in additional modules to verify and
            possibly alter the move lines to be created by an invoice, for
            special cases.
            :param move_lines: list of dictionaries with the account.move.lines (as for create())
            :return: the (possibly updated) final move_lines to create for this invoice
        """
        return move_lines

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.expense_line_ids.filtered(lambda line: line.account_id):
                raise UserError(_('Please add at least one invoice line.'))
            if inv.move_id:
                continue


            if not inv.date_invoice:
                inv.write({'date_invoice': fields.Date.context_today(self)})
            if not inv.date_due:
                inv.write({'date_due': inv.date_invoice})
            company_currency = inv.company_id.currency_id
            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()
            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.compute_invoice_totals(company_currency, iml)
            name = inv.name or ''
            iml.append({
                'type': 'dest',
                'name': name,
                'price': total,
                'account_id': inv.account_id.id,
                'date_maturity': inv.date_due,
                'amount_currency': diff_currency and total_currency,
                'currency_id': diff_currency and inv.currency_id.id,
                'expense_provision_id': inv.id
            })
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)

            line = inv.finalize_invoice_move_lines(line)
            date = inv.date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': inv.journal_id.id,
                'date': date,
                'narration': inv.comment,
            }
            move = account_move.create(move_vals)
            move.post()
            vals = {
                'move_id': move.id,
                'move_name': move.name,
                'name': move.name,
            }
            inv.write(vals)
        return True

    @api.multi
    def expense_validate(self):
        return self.write({'state': 'open'})

    @api.multi
    def action_expense_open(self):
        date_invoice = self.date_invoice
        if not date_invoice:
            date_invoice = fields.Date.context_today(self)
            self.date_invoice = date_invoice
        self.action_move_create()
        return self.expense_validate()

    def _prepare_tax_line_vals(self, line, tax):
        """ Prepare values to create an account.invoice.tax line

        The line parameter is an account.invoice.line, and the
        tax parameter is the output of account.tax.compute_all().
        """
        vals = {
            'expense_provision_id': self.id,
            'name': tax['name'],
            'tax_id': tax['id'],
            'amount': tax['amount'],
            'base': tax['base'],
            'manual': False,
            'sequence': tax['sequence'],
            'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
            'account_id': tax['refund_account_id'] or line.account_id.id,
        }
        return vals

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.expense_line_ids:
            if not line.account_id:
                continue
            price_unit = line.price_unit
            taxes = line.provision_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped

    @api.onchange('expense_line_ids')
    def _onchange_invoice_line_ids(self):
        taxes_grouped = self.get_taxes_values()
        tax_lines = self.tax_line_ids.filtered('manual')
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)
        self.tax_line_ids = tax_lines
        return

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        account_id = False
        payment_term_id = False
        fiscal_position = False
        warning = {}
        domain = {}
        company_id = self.company_id.id
        part = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
        if part:
            rec_account = part.property_account_receivable_id
            pay_account = part.property_account_payable_id
            if not rec_account and not pay_account:
                action = self.env.ref('account.action_account_config')
                msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
            account_id = pay_account.id
            # If partner has no warning, check its company
            if part.invoice_warn == 'no-message' and part.parent_id:
                part = part.parent_id
            if part.invoice_warn and part.invoice_warn != 'no-message':
                # Block if partner only has warning but parent company is blocked
                if part.invoice_warn != 'block' and part.parent_id and part.parent_id.invoice_warn == 'block':
                    part = part.parent_id
                warning = {
                    'title': _("Warning for %s") % part.name,
                    'message': part.invoice_warn_msg
                }
                if part.invoice_warn == 'block':
                    self.partner_id = False

        self.account_id = account_id
        self.payment_term_id = payment_term_id
        self.date_due = False
        self.fiscal_position_id = fiscal_position
        res = {}
        if warning:
            res['warning'] = warning
        if domain:
            res['domain'] = domain
        return res

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']
        account_id = False
        if so_line.product_id.id:
            account_id = so_line.product_id.property_account_income_id.id or so_line.product_id.categ_id.property_account_income_categ_id.id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(_('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %(self.product_id.name,))

        taxes = so_line.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
        if order.fiscal_position_id and taxes:
            tax_ids = order.fiscal_position_id.map_tax(taxes, so_line.product_id, order.partner_shipping_id).ids
        else:
            tax_ids = taxes.ids

        invoice = inv_obj.create({
            'name': order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': self.name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': so_line.price_unit,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': so_line.product_id.uom_id.id,
                'product_id': so_line.product_id.id,
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
            })],
            'currency_id': order.currency_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'user_id': order.user_id.id,
            'comment': order.comment,
        })
        invoice.compute_taxes()
        invoice.message_post_with_view('mail.message_origin_link',values={'self': invoice, 'origin': order}, subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    @api.multi
    def action_create_invoice(self):
        inv_obj = self.env['account.invoice']
        if self.invoice_id.id:
            raise Warning('Already Invoiced')
        lines = []
        tax_ids = []
        if not self.expense_line_ids:
            raise Warning('No lines')
        for line in self.expense_line_ids:

            taxes = line.product_id.taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
            if self.fiscal_position_id and taxes:
                tax_ids = self.fiscal_position_id.map_tax(taxes, line.product_id, line.partner_id).ids
            if tax_ids:
                pass
            else:
                tax_ids = taxes.ids
            line_dict = {}
            line_dict['invoice_line_tax_ids'] = [(6, 0, tax_ids)]
            line_dict['product_id'] = line.product_id.id

            line_dict['name'] = line.name
            line_dict['origin'] = self.number
            line_dict['account_id'] = line.account_id.id
            line_dict['price_unit'] = line.price_unit
            line_dict['product_id'] = line.product_id.id
            line_dict['quantity'] = line.quantity
            line_dict['uom_id'] = line.product_id.uom_id.id
            lines.append((0, 0, line_dict))


        invoice = inv_obj.create({
            'state': 'draft',
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'type': 'in_invoice',
            'reference': self.name,
            'account_id': self.partner_id.property_account_receivable_id.id,
            'invoice_line_ids': lines
        })
        self.state = 'invoiced'
        self.invoice_id = invoice.id
        self.rt_service_product_id.supplier_invoices_ids = invoice
        self.rt_service_product_id.rt_service_id.supplier_invoices_ids = invoice





class ExpenseProvisionLine(models.Model):
    _name = "expense.provision.line"
    _description = "Provision Line"
    _order = "expense_provision_id,sequence,id"

    @api.one
    @api.depends('price_unit', 'provision_line_tax_ids', 'quantity',
                 'product_id', 'expense_provision_id.partner_id', 'expense_provision_id.currency_id', 'expense_provision_id.company_id',
                 'expense_provision_id.date_invoice')
    def _compute_price(self):
        currency = self.expense_provision_id and self.expense_provision_id.currency_id or None
        price = self.price_unit
        taxes = False
        if self.provision_line_tax_ids:
            taxes = self.provision_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id, partner=self.expense_provision_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal
        if self.expense_provision_id.currency_id and self.expense_provision_id.currency_id != self.expense_provision_id.company_id.currency_id:
            currency = self.expense_provision_id.currency_id
            date = self.expense_provision_id._get_currency_rate_date()
            price_subtotal_signed = currency._convert(price_subtotal_signed, self.expense_provision_id.company_id.currency_id, self.company_id or self.env.user.company_id, date or fields.Date.today())

    @api.model
    def _default_account(self):
        if self._context.get('journal_id'):
            journal = self.env['account.journal'].browse(self._context.get('journal_id'))
            return journal.default_debit_account_id.id

    def _get_price_tax(self):
        for l in self:
            l.price_tax = l.price_total - l.price_subtotal

    name = fields.Text(string='Description', required=True)
    origin = fields.Char(string='Source Document', help="Reference of the document that produced this invoice.")
    sequence = fields.Integer(default=10, help="Gives the sequence of this line when displaying the invoice.")
    expense_provision_id = fields.Many2one('expense.provision', string='Invoice Reference',ondelete='cascade', index=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure',ondelete='set null', index=True, oldname='uos_id')
    product_id = fields.Many2one('product.product', string='Product',ondelete='restrict', index=True)
    product_image = fields.Binary('Product Image', related="product_id.image", store=False, readonly=True)
    account_id = fields.Many2one('account.account', string='Account', domain=[('deprecated', '=', False)],default=_default_account,help="The income or expense account related to the selected product.")
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Monetary(string='Amount (without Taxes)',store=True, readonly=True, compute='_compute_price', help="Total amount without taxes")
    price_total = fields.Monetary(string='Amount (with Taxes)', store=True, readonly=True, compute='_compute_price', help="Total amount with taxes")
    price_tax = fields.Monetary(string='Tax Amount', compute='_get_price_tax', store=False)
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'),required=True, default=1)
    company_id = fields.Many2one('res.company', string='Company', related='expense_provision_id.company_id', store=True, readonly=True, related_sudo=False)
    partner_id = fields.Many2one('res.partner', string='Partner', related='expense_provision_id.partner_id', store=True, readonly=True, related_sudo=False)
    currency_id = fields.Many2one('res.currency', related='expense_provision_id.currency_id', store=True, related_sudo=False, readonly=False)
    provision_line_tax_ids = fields.Many2many('account.tax', 'expense_provision_line_tax', 'expense_provision_line_id', 'tax_id', string='Taxes',
                                              domain=[('type_tax_use','!=','none'), '|', ('active', '=', False), ('active', '=', True)])


    @api.v8
    def get_invoice_line_account(self, type, product, fpos, company):
        accounts = product.product_tmpl_id.get_product_accounts(fpos)
        return accounts['expense']

    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {}
        if not self.expense_provision_id:
            return

        part = self.expense_provision_id.partner_id
        company = self.expense_provision_id.company_id
        if not part:
            warning = {
                'title': _('Warning!'),
                'message': _('You must first select a partner.'),
            }
            return {'warning': warning}

        if not self.product_id:
            self.price_unit = 0.0
            domain['uom_id'] = []
        else:
            if part.lang:
                product = self.product_id.with_context(lang=part.lang)
            else:
                product = self.product_id

            account = self.get_invoice_line_account('in_invoice', product, False, company)
            if account:
                self.account_id = account.id
            self._set_taxes()

            product_name = self._get_invoice_line_name_from_product()
            if product_name != None:
                self.name = product_name

            domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]
        return {'domain': domain}


    def _get_invoice_line_name_from_product(self):
        """ Returns the automatic name to give to the invoice line depending on
        the product it is linked to.
        """
        self.ensure_one()
        if not self.product_id:
            return ''
        rslt = self.product_id.partner_ref
        if self.product_id.description_sale:
            rslt += '\n' + self.product_id.description_sale

        return rslt

    def _set_currency(self):
        company = self.expense_provision_id.company_id
        currency = self.expense_provision_id.currency_id
        if company and currency:
            if company.currency_id != currency:
                self.price_unit = self.price_unit * currency.with_context(dict(self._context or {}, date=self.expense_provision_id.date_invoice)).rate

    def _set_taxes(self):
        """ Used in on_change to set taxes and price"""
        self.ensure_one()

        taxes = self.product_id.supplier_taxes_id or self.account_id.tax_ids or self.expense_provision_id.company_id.account_purchase_tax_id

        # Keep only taxes of the company
        company_id = self.company_id or self.env.user.company_id
        taxes = taxes.filtered(lambda r: r.company_id == company_id)

        self.provision_line_tax_ids = fp_taxes = self.expense_provision_id.fiscal_position_id.map_tax(taxes, self.product_id, self.expense_provision_id.partner_id)

        fix_price = self.env['account.tax']._fix_tax_included_price
        self.price_unit = fix_price(self.product_id.lst_price, taxes, fp_taxes)
        self._set_currency()



class ExpenseProvisionTax(models.Model):
    _name = "expense.provision.tax"
    _description = "Expense Provision Tax"
    _order = 'sequence'

    @api.depends('expense_provision_id.expense_line_ids')
    def _compute_base_amount(self):
        tax_grouped = {}
        for invoice in self.mapped('expense_provision_id'):
            tax_grouped[invoice.id] = invoice.get_taxes_values()
        for tax in self:
            tax.base = 0.0
            if tax.tax_id:
                key = tax.tax_id.get_grouping_key({
                    'tax_id': tax.tax_id.id,
                    'account_id': tax.account_id.id,
                    'account_analytic_id': tax.account_analytic_id.id,
                    'analytic_tag_ids': tax.analytic_tag_ids.ids or False,
                })
                if tax.expense_provision_id and key in tax_grouped[tax.expense_provision_id.id]:
                    tax.base = tax_grouped[tax.expense_provision_id.id][key]['base']
                else:
                    _logger.warning('Tax Base Amount not computable probably due to a change in an underlying tax (%s).', tax.tax_id.name)

    expense_provision_id = fields.Many2one('expense.provision', string='Invoice', ondelete='cascade', index=True)
    name = fields.Char(string='Tax Description', required=True)
    tax_id = fields.Many2one('account.tax', string='Tax', ondelete='restrict')
    account_id = fields.Many2one('account.account', string='Tax Account', required=True, domain=[('deprecated', '=', False)])
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    amount = fields.Monetary('Tax Amount')
    amount_rounding = fields.Monetary('Amount Delta')
    amount_total = fields.Monetary(string="Amount Total", compute='_compute_amount_total')
    manual = fields.Boolean(default=True)
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of invoice tax.")
    company_id = fields.Many2one('res.company', string='Company', related='account_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='expense_provision_id.currency_id', store=True, readonly=True)
    base = fields.Monetary(string='Base', compute='_compute_base_amount', store=True)

    @api.depends('amount', 'amount_rounding')
    def _compute_amount_total(self):
        for tax_line in self:
            tax_line.amount_total = tax_line.amount + tax_line.amount_rounding