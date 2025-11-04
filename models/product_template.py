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
                    res['company_ids'] = [(6, 0, [company.id])]
                    _logger.info(
                        "[default_get] Asignado company_ids='%s' (%s) al producto por defecto '%s' (usuario: %s)",
                        company.id, company.name, res.get('name', 'Sin nombre'), user.login
                    )
                else:
                    _logger.warning(
                        "[default_get] No se pudo determinar la compañía activa para el usuario '%s'. No se asignó company_ids al producto %s.",
                        user.login, res.get('name', 'Sin nombre')
                    )
            except Exception as e:
                _logger.exception(
                    "[default_get] Error inesperado al asignar company_ids por defecto al producto '%s': %s",
                    res.get('name', 'Sin nombre'), e
                )

        return res

    @api.model_create_multi
    def create(self, vals_list):
        user = self.env.user
        company = (
            self.env.company if len(user.company_ids) > 1
            else user.company_id
        )

        for vals in vals_list:
            try:
                product_name = vals.get('name', 'Sin nombre')

                if 'company_ids' not in vals and company:
                    vals['company_ids'] = [(6, 0, [company.id])]
                    _logger.info(
                        "[create] Asignado company_ids='%s' (%s) al producto '%s' (usuario: %s)",
                        company.id, company.name, product_name, user.login
                    )
                elif 'company_ids' not in vals:
                    _logger.warning(
                        "[create] No se pudo determinar la compañía activa. Se omitió company_ids para el producto '%s' (usuario: %s)",
                        product_name, user.login
                    )
            except Exception as e:
                _logger.exception(
                    "[create] Error al intentar asignar company_ids al producto '%s': %s",
                    vals.get('name', 'Sin nombre'), e
                )

        return super().create(vals_list)
