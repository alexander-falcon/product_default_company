# -*- coding: utf-8 -*-

from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        if 'company_ids' in fields_list and not res.get('company_ids'):
            try:
                user = self.env.user
                company = (
                    self.env.company if len(user.company_ids) > 1
                    else user.company_id
                )
                if company:
                    context_company = self.env.context.get('default_company_ids')
                    if not context_company:
                        company_sudo = company.sudo()
                        res['company_ids'] = [(6, 0, [company_sudo.id])]
                        _logger.info(
                            "[default_get] Asignado company_ids='%s' (%s) a producto por defecto (usuario: %s, compañías permitidas: %s)",
                            company_sudo.id, company_sudo.name, 
                            user.login, len(user.company_ids)
                        )
                    else:
                        _logger.info(
                            "[default_get] Se respeta compañía del contexto: %s",
                            context_company
                        )
                else:
                    _logger.warning(
                        "[default_get] No se pudo determinar la compañía activa para el usuario '%s'. No se asignó company_ids al producto.",
                        user.login
                    )
            except Exception as e:
                _logger.exception("[default_get] Error inesperado : %s",
                    e
                )
        return res

    @api.model_create_multi
    def create(self, vals_list):
        user = self.env.user
        company = (
            self.env.company if len(user.company_ids) > 1
            else user.company_id
        )
        processed_vals_list = []
        for vals in vals_list:
            try:
                product_name = vals.get('name', 'Sin nombre')
                new_vals = vals.copy()

                if 'company_ids' not in vals and company:
                    company_sudo = company.sudo()
                    new_vals['company_ids'] = [(6, 0, [company_sudo.id])]
                    _logger.info(
                        "[create] Asignado company_ids='%s' (%s) al producto '%s' (usuario: %s)",
                        company_sudo.id, company_sudo.name, product_name, user.login
                    )
                elif 'company_ids' in vals:
                    _logger.info(
                        "[create] Producto '%s' ya tenía company_ids definido en vals, se respeta: %s",
                        product_name, vals['company_ids']
                    )
                else:
                    _logger.warning(
                        "[create] No hay compañía activa para asignar al producto '%s'",
                        product_name
                    )
                processed_vals_list.append(new_vals)
            except Exception as e:
                _logger.exception(
                    "[create] Error al intentar asignar company_ids al producto '%s': %s",
                    product_name, e
                )
                processed_vals_list.append(vals)

        products = super(ProductTemplate, self.sudo()).create(processed_vals_list)

        _logger.info(
            "[create] Creados %d productos con sudo() para el usuario %s",
            len(products), user.login
        )
        
        return products
        