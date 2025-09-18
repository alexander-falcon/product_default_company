# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    '''@api.model
    def default_get(self, fields_list):
        res = super(ProductTemplate, self).default_get(fields_list)
        if 'company_ids' in fields_list and not res.get('company_ids'):
            current_company = self.env.company
            res['company_ids'] = [(6, 0, [current_company.id])]
        return res'''
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'company_ids' in fields_list and not res.get('company_ids'):
            try:
                user_company = self.env.user.company_id
                if user_company:
                    res['company_ids'] = [(6, 0, [user_company.id])]
            except Exception as e:
                _logger.warning("Failed to set default company: %s", e)
        return res