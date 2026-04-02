# -*- coding: utf-8 -*-

from odoo.tests import common, tagged
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


@tagged('security', 'post_install')
class TestProductCompanyAutoAssignSecurity(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Crear compañías
        cls.company_obj = cls.env['res.company']
        cls.company_a = cls.company_obj.create({'name': 'Company A'})
        cls.company_b = cls.company_obj.create({'name': 'Company B'})

        group_account = cls.env.ref('account.group_account_manager', raise_if_not_found=False)
        group_ids = [group_account.id]
        
        # Crear usuarios
        cls.user_a = cls.env['res.users'].create({
            'name': 'User A',
            'login': 'user_a',
            'company_id': cls.company_a.id,
            'company_ids': [(6, 0, [cls.company_a.id])],
            'groups_id': [(6, 0, group_ids)],
        })
        
        cls.user_b = cls.env['res.users'].create({
            'name': 'User B',
            'login': 'user_b',
            'company_id': cls.company_b.id,
            'company_ids': [(6, 0, [cls.company_b.id])],
            'groups_id': [(6, 0, group_ids)],
        })

    def test_security_cannot_assign_other_company(self):
        """Test: Un usuario no debe poder asignar company_ids de otra compañía"""
        product = self.env['product.template'].with_user(
            self.user_a
        ).create({
            'name': 'Product User A',
        })
        
        # Intentar modificar company_ids a compañía B
        with self.assertRaises(AccessError):
            product.with_user(self.user_a).write({
                'company_ids': [(6, 0, [self.company_b.id])]
            })
        
        _logger.info("✓ Seguridad: No se puede asignar compañía ajena")

    def test_security_own_company_modification(self):
        """Test: Usuario puede modificar productos de su compañía"""
        product = self.env['product.template'].with_user(
            self.user_a
        ).create({
            'name': 'Product User A',
        })
        
        # Modificar nombre - debe funcionar
        try:
            product.with_user(self.user_a).write({'name': 'Modified Product'})
        except AccessError:
            self.fail("Usuario debe poder modificar producto de su compañía")
        
        self.assertEqual(product.name, 'Modified Product')
        _logger.info("✓ Usuario puede modificar productos de su compañía")