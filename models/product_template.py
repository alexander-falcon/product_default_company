# -*- coding: utf-8 -*-

from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _get_company_vals(self, values, check_context=True):
        user = self.env.user
        company = (
            self.env.company if len(user.company_ids) > 1
            else user.company_id
        )
        
        if not company:
            return values
            
        company_sudo = company.sudo()
        
        if 'company_id' not in values:
            if not (check_context and self.env.context.get('default_company_id')):
                values['company_id'] = company_sudo.id
                _logger.info(
                    "Asignado company_id=%s (%s) por usuario %s",
                    company_sudo.id, company_sudo.name, user.login
                )
        
        if 'company_ids' not in values:
            if not (check_context and self.env.context.get('default_company_ids')):
                values['company_ids'] = [(6, 0, [company_sudo.id])]
                _logger.info(
                    "Asignado company_ids=%s (%s) por usuario %s",
                    company_sudo.id, company_sudo.name, user.login
                )
        
        return values
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        company_fields = [f for f in ['company_id', 'company_ids'] if f in fields_list]
        if not company_fields:
            return res
            
        try:
            res = self._get_company_vals(res, check_context=True)
        except Exception as e:
            _logger.exception("[default_get] Error inesperado: %s", e)
            
        return res

    @api.model_create_multi
    def create(self, vals_list):
        processed_vals_list = []
        
        for vals in vals_list:
            try:
                new_vals = vals.copy()
                new_vals = self._get_company_vals(new_vals, check_context=False)
                processed_vals_list.append(new_vals)
            except Exception as e:
                _logger.exception(
                    "[create] Error procesando vals: %s", e
                )
                processed_vals_list.append(vals)

        products = super(ProductTemplate, self.sudo()).create(processed_vals_list)

        _logger.info(
            "[create] Creados %d productos para usuario %s",
            len(products), self.env.user.login
        )
        
        return products
    