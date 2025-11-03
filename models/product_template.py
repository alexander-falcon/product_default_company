# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import ValidationError
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
                if user.has_group('base.group_system'):
                    active_company = self.env.company
                    if active_company:
                        res['company_ids'] = [(6, 0, [active_company.id])]
                        _logger.info("Asignando company_ids desde env.company para administrador: %s", active_company.name)
                    else:
                        _logger.warning("No se pudo obtener la compañía activa desde env.company")
                else:
                    user_company = user.company_id
                    if user_company:
                        res['company_ids'] = [(6, 0, [user_company.id])]
                        _logger.info("Asignando company_ids desde user.company_id para usuario: %s", user_company.name)
                    else:
                        _logger.warning("El usuario no tiene una compañía principal asignada")
            except Exception as e:
                _logger.warning("Error al asignar company_ids en default_get: %s", e)
        return res

    @api.model
    def create(self, vals):
        if not vals.get('company_ids'):
            try:
                user = self.env.user if self.env.user.id != SUPERUSER_ID else self.env['res.users'].browse(SUPERUSER_ID)
                if user.has_group('base.group_system'):
                    active_company = self.env.company
                    if active_company:
                        vals['company_ids'] = [(6, 0, [active_company.id])]
                        _logger.info("Asignando company_ids desde env.company para administrador: %s", active_company.name)
                else:
                    user_company = user.company_id
                    if user_company:
                        vals['company_ids'] = [(6, 0, [user_company.id])]
                        _logger.info("Asignando company_ids desde user.company_id para usuario: %s", user_company.name)
            except Exception as e:
                _logger.warning("Error al asignar company_ids en create: %s", e)
        return super().create(vals)

    def write(self, vals):
        if self.env.context.get('skip_company_check'):
            return super().write(vals)
        res = super().write(vals)
        for record in self:
            if not record.company_ids:
                try:
                    user = self.env.user if self.env.user.id != SUPERUSER_ID else self.env['res.users'].browse(SUPERUSER_ID)
                    user_company = user.company_id
                    if user_company:
                        record.with_context(skip_company_check=True).sudo().write({
                            'company_ids': [(6, 0, [user_company.id])]
                        })
                        _logger.info("Restaurando company_ids para producto '%s' con la compañía del usuario: %s", record.name, user_company.name)
                    else:
                        _logger.warning("No se pudo obtener una compañía válida desde el usuario para restaurar company_ids en '%s'", record.name)
                except Exception as e:
                    _logger.warning("Error al restaurar company_ids en write: %s", e)
        return res

    @api.constrains('company_ids')
    def _check_company_ids(self):
        if self.env.context.get('skip_company_check'):
            return
        for record in self:
            if not record.company_ids:
                raise ValidationError("No se puede dejar el campo 'company_ids' vacío en el producto.")
    