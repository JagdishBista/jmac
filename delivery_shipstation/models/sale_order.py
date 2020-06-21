# -*- coding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2020 (https://www.bistasolutions.com)
#
##############################################################################
from odoo import models, fields, api, _
import operator


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line')
    def _compute_order_weight(self):
        for order in self:
            order.order_quantity = int(
                sum(order.order_line.filtered(lambda l: not l.is_delivery).mapped('product_uom_qty')))
            line_with_weight = order.order_line.filtered(lambda line: line.product_id.weight > 0.00)
            order.order_weight = sum([(line.product_qty * line.product_id.weight) for line in line_with_weight])
            # order.order_weight = sum(line.product_id.weight for line in order.order_line)

    rule_id = fields.Many2one("automation.rule", string="Rule", copy=False)
    order_weight = fields.Float(compute='_compute_order_weight', string='Order Weight')
    order_quantity = fields.Integer(compute='_compute_order_weight', string='Order Quantity')

    def apply_automation_rule(self):
        automation_rule_ids = self.env['automation.rule'].search([])
        val_dict = {}
        for rule in automation_rule_ids:
            matched_rule = True
            for line in rule.rule_line:
                if line.category_type in ('qty', 'wgt', 'val'):
                    opr_val = str(line.operator_type_id.operator) + ' ' + str(line.value)
                if line.category_type == 'qty':
                    str_c = str(self.order_quantity) + ' ' + opr_val
                elif line.category_type == 'wgt':
                    str_c = str(self.order_weight) + ' ' + opr_val
                elif line.category_type == 'val':
                    str_c = str(self.amount_untaxed) + ' ' + opr_val
                if not eval(str_c):
                    matched_rule = False
                    break
            if matched_rule:
                val_dict.update({
                    'rule_id': rule.id,
                })
                for action in rule.rule_action_line:
                    if action.action_type == 'tag':
                        pass
                    if action.action_type == 'dimension':
                        val_dict.update({
                            'length': action.length,
                            'width': action.width,
                            'height': action.height,
                        })
                    if action.action_type == 'carrier':
                        val_dict.update({
                            'carrier_id': action.service_id and action.service_id.id or False,
                            'ship_package_id': action.package_id and action.package_id.id or False,
                        })
                    if action.action_type == 'insure':
                        val_dict.update({
                            'insure_package_type': action.insure_package_type,
                        })
                    if action.action_type == 'weight':
                        val_dict.update({
                            'shipping_weight': action.shipping_weight_lb,
                            'shipping_weight_oz': action.shipping_weight_oz,
                        })
                self.rule_id = rule.id
                break
            else:
                self.rule_id = False
        return val_dict

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.picking_ids:
            pickings = self.picking_ids.filtered(
                lambda x: x.state == 'confirmed' or (x.state in ['waiting', 'assigned']))
            rule_dict = self.apply_automation_rule()
            if rule_dict:
                pickings.with_context(api_call=True).write(rule_dict)
            else:
                default_carrier_id = self.env['shipstation.carrier'].search([('code', '=', 'stamps_com')])
                pickings.write({'shipstation_carrier_id': default_carrier_id.id,
                                'carrier_id': False, })
            pickings.with_context(api_call=True).get_shipping_rates()
        return res
