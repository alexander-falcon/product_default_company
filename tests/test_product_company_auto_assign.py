# -*- coding: utf-8 -*-

from odoo.tests import common, tagged
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestProductCompanyAutoAssign(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Deshabilitar tracking para mejorar rendimiento en pruebas
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Crear compañías de prueba
        cls.company_obj = cls.env['res.company']
        cls.company_1 = cls.company_obj.create({'name': 'Test Company 1'})
        cls.company_2 = cls.company_obj.create({'name': 'Test Company 2'})
        
        # Crear usuarios con diferentes compañías
        cls.user_company_1 = cls.env['res.users'].create({
            'name': 'User Company 1',
            'login': 'user_company_1',
            'email': 'user1@test.com',
            'company_id': cls.company_1.id,
            'company_ids': [(6, 0, [cls.company_1.id])],
        })
        
        cls.user_company_2 = cls.env['res.users'].create({
            'name': 'User Company 2',
            'login': 'user_company_2',
            'email': 'user2@test.com',
            'company_id': cls.company_2.id,
            'company_ids': [(6, 0, [cls.company_2.id])],
        })
        
        # Usuario con múltiples compañías
        cls.user_multi_company = cls.env['res.users'].create({
            'name': 'Multi Company User',
            'login': 'user_multi',
            'email': 'multi@test.com',
            'company_id': cls.company_1.id,
            'company_ids': [(6, 0, [cls.company_1.id, cls.company_2.id])],
        })
        
        # Usuario administrador (superusuario) para pruebas de sudo
        cls.user_admin = cls.env.ref('base.user_admin')
        
        _logger.info("SetUp completado: Compañías y usuarios creados")

    def test_01_create_product_single_company_user(self):
        """Test: Usuario con una sola compañía - debe asignar company_ids automáticamente"""
        product = self.env['product.template'].with_user(
            self.user_company_1
        ).create({
            'name': 'Product Single Company',
        })
        
        # Verificar que company_ids se asignó automáticamente
        self.assertTrue(product.company_ids, "company_ids debería tener valor")
        self.assertEqual(
            product.company_ids.ids,
            [self.company_1.id],
            "company_ids debería ser la compañía del usuario"
        )
        _logger.info("✓ Producto creado con company_ids=%s", product.company_ids.ids)

    def test_02_create_product_multi_company_user(self):
        """Test: Usuario con múltiples compañías - debe asignar company_ids correctamente"""
        product = self.env['product.template'].with_user(
            self.user_multi_company
        ).create({
            'name': 'Product Multi Company',
        })
        
        # El usuario tiene múltiples compañías, debe asignar la compañía principal
        self.assertTrue(product.company_ids, "company_ids debería tener valor")
        self.assertEqual(
            product.company_ids.ids,
            [self.company_1.id],
            "company_ids debería ser la compañía principal del usuario"
        )
        _logger.info("✓ Producto multi-compañía creado con company_ids=%s", product.company_ids.ids)

    def test_03_create_product_with_company_ids_manual(self):
        """Test: Crear producto especificando company_ids manualmente - no debe sobrescribir"""
        product = self.env['product.template'].with_user(
            self.user_company_1
        ).create({
            'name': 'Product Manual Company',
            'company_ids': [(6, 0, [self.company_2.id])],
        })
        
        # No debe sobrescribir el company_ids manual
        self.assertEqual(
            product.company_ids.ids,
            [self.company_2.id],
            "No debe sobrescribir company_ids especificado manualmente"
        )
        _logger.info("✓ Producto con company_ids manual respetado")

    def test_04_create_product_with_default_company_ids_context(self):
        """Test: Crear producto con default_company_ids en contexto"""
        product = self.env['product.template'].with_context(
            default_company_ids=[(6, 0, [self.company_2.id])]
        ).with_user(self.user_company_1).create({
            'name': 'Product Context Default',
        })
        
        # Debe respetar el default_company_ids del contexto
        self.assertEqual(
            product.company_ids.ids,
            [self.company_2.id],
            "Debe respetar default_company_ids del contexto"
        )
        _logger.info("✓ Producto respeta default_company_ids del contexto")

    def test_05_create_multiple_products(self):
        """Test: Creación múltiple de productos (create multi)"""
        products = self.env['product.template'].with_user(
            self.user_company_1
        ).create([
            {'name': 'Product Multi 1'},
            {'name': 'Product Multi 2'},
            {'name': 'Product Multi 3'},
        ])
        
        # Verificar que todos los productos tienen company_ids asignado
        for product in products:
            self.assertTrue(product.company_ids, "Todos los productos deben tener company_ids")
            self.assertEqual(
                product.company_ids.ids,
                [self.company_1.id],
                "Todos deben tener la compañía del usuario"
            )
        
        self.assertEqual(len(products), 3, "Deben crearse 3 productos")
        _logger.info("✓ Creados %d productos correctamente", len(products))

    def test_07_default_get_method(self):
        """Test: Método default_get - debe incluir company_ids por defecto"""
        default_vals = self.env['product.template'].with_user(
            self.user_company_1
        ).default_get(['name', 'company_id', 'company_ids'])
        
        # Verificar que company_ids está en los valores por defecto
        self.assertIn('company_ids', default_vals, "default_get debe incluir company_ids")
        
        # Verificar que el valor es correcto
        if default_vals.get('company_ids'):
            self.assertEqual(
                default_vals['company_ids'][0][2],
                [self.company_1.id],
                "El valor por defecto debe ser la compañía del usuario"
            )
        _logger.info("✓ default_get funciona correctamente")

    def test_08_create_with_company_id_field(self):
        """Test: Crear producto usando company_id (campo de multi.company.abstract)"""
        # Usar el campo company_id que viene de multi.company.abstract
        product = self.env['product.template'].with_user(
            self.user_company_1
        ).create({
            'name': 'Product With Company ID',
            'company_id': self.company_2.id,  # Usar company_id
        })
        
        # Debe asignar correctamente company_ids
        self.assertTrue(product.company_ids, "company_ids debe tener valor")
        self.assertEqual(
            product.company_ids.ids,
            [self.company_2.id],
            "company_ids debe reflejar el company_id especificado"
        )
        _logger.info("✓ Producto creado con company_id correctamente")

    def test_11_create_with_empty_values(self):
        """Test: Crear producto con valores vacíos (edge case)"""
        product = self.env['product.template'].with_user(
            self.user_company_1
        ).create({
            'name': '',
        })
        
        # Debe asignar company_ids aunque el nombre esté vacío
        self.assertTrue(product.company_ids, "company_ids debe asignarse aunque nombre esté vacío")
        _logger.info("✓ Edge case con valores vacíos manejado correctamente")

    def test_12_update_product_company(self):
        """Test: Actualizar company_ids de un producto existente"""
        product = self.env['product.template'].with_user(
            self.user_company_1
        ).create({
            'name': 'Product to Update',
        })
        
        # Verificar estado inicial
        self.assertEqual(product.company_ids.ids, [self.company_1.id])
        
        # Usar sudo() para tener permisos de escritura
        product.sudo().write({
            'company_ids': [(6, 0, [self.company_2.id])]
        })
        
        # Verificar actualización
        self.assertEqual(
            product.company_ids.ids,
            [self.company_2.id],
            "Debe poder actualizar company_ids"
        )
        _logger.info("✓ Actualización de company_ids funciona correctamente")
    
    def test_13_update_with_company_id(self):
        """Test: Actualizar producto usando company_id"""
        product = self.env['product.template'].with_user(
            self.user_company_1
        ).create({
            'name': 'Product to Update',
        })
        
        # Verificar estado inicial
        self.assertEqual(product.company_ids.ids, [self.company_1.id])
        
        # Actualizar usando company_id
        product.sudo().write({
            'company_id': self.company_2.id
        })
        
        # Verificar que company_ids se actualizó
        self.assertEqual(
            product.company_ids.ids,
            [self.company_2.id],
            "Actualizar company_id debe actualizar company_ids"
        )
        _logger.info("✓ Actualización con company_id funciona correctamente")

    def test_14_copy_product(self):
        """Test: Copiar producto debe mantener o cambiar company_ids"""
        original = self.env['product.template'].with_user(
            self.user_company_1
        ).create({
            'name': 'Original Product',
        })
        
        # Copiar el producto
        copy = original.with_user(self.user_company_1).copy()
        
        # Verificar que la copia tiene company_ids
        self.assertTrue(copy.company_ids, "La copia debe tener company_ids")
        self.assertEqual(
            copy.company_ids.ids,
            [self.company_1.id],
            "La copia debe mantener la compañía"
        )
        _logger.info("✓ Copia de producto funciona correctamente")


    def test_16_unique_company_constraint(self):
        """Test: No debe permitir company_ids duplicados"""
        
        # Intentar crear producto con company_ids duplicados (mismo ID dos veces)
        # Nota: Esto debería manejarse automáticamente por Odoo
        product = self.env['product.template'].with_user(
            self.user_company_1
        ).create({
            'name': 'Unique Test',
            'company_ids': [(6, 0, [self.company_1.id, self.company_1.id])],
        })
        
        # Odoo debería deduplicar automáticamente
        self.assertEqual(
            len(product.company_ids.ids),
            1,
            "No debe permitir compañías duplicadas"
        )
        _logger.info("✓ No se permiten compañías duplicadas")