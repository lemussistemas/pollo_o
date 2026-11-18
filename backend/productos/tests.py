from django.test import TestCase
from rest_framework.test import APIClient

from accounts.seed import DEMO_PASSWORD, seed
from clientes.models import Cliente, PuntoVenta
from productos.models import Producto


class ProductoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        punto = PuntoVenta.objects.get(code="pulperias")
        from django.contrib.auth import get_user_model

        vendedor = get_user_model().objects.get(username="vendedor")
        cls.suyo = Cliente.objects.create(nombre="Pulpería de la ruta", punto=punto, vendedor=vendedor)
        cls.ajeno = Cliente.objects.create(nombre="Otro cliente", punto=punto)

    def login(self, username):
        client = APIClient()
        response = client.post(
            "/api/auth/login/",
            {"username": username, "password": DEMO_PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return client

    def test_inventario_creates_and_facturacion_sets_the_customer_price(self):
        inventario = self.login("inventario")
        created = inventario.post(
            "/api/productos/",
            {"nombre": "Alitas", "unidad": "libra", "precio_base": "42.00", "controla_lote": True},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.content)
        self.assertTrue(created.data["codigo"].startswith("PR-"))
        self.assertEqual(created.data["unidad_label"], "Libra")
        product_id = created.data["id"]

        blocked = self.login("facturacion")
        denied = blocked.post(
            "/api/productos/",
            {"nombre": "No debe", "unidad": "unidad", "precio_base": "1.00"},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)

        missing = blocked.post(
            f"/api/productos/{product_id}/precios/",
            {"cliente_id": self.suyo.id, "precio": "0"},
            format="json",
        )
        self.assertEqual(missing.status_code, 400)

        priced = blocked.post(
            f"/api/productos/{product_id}/precios/",
            {"cliente_id": self.suyo.id, "precio": "48.50"},
            format="json",
        )
        self.assertEqual(priced.status_code, 200, priced.content)
        self.assertEqual(priced.data["precios"][0]["precio"], "48.50")

        inventario_price = inventario.post(
            f"/api/productos/{product_id}/precios/",
            {"cliente_id": self.ajeno.id, "precio": "50.00"},
            format="json",
        )
        self.assertEqual(inventario_price.status_code, 403)

        gerencia = self.login("gerencia")
        gerencia.post(
            f"/api/productos/{product_id}/precios/",
            {"cliente_id": self.ajeno.id, "precio": "55.00"},
            format="json",
        )
        product = Producto.objects.get(pk=product_id)
        self.assertEqual(str(product.precio_para(self.suyo)), "48.50")
        self.assertEqual(str(product.precio_para(self.ajeno)), "55.00")

    def test_vendedor_only_sees_prices_of_his_clients(self):
        product = Producto.objects.create(nombre="Pechuga", unidad="unidad", precio_base="30.00")
        from productos.models import PrecioCliente

        PrecioCliente.objects.create(producto=product, cliente=self.suyo, precio="33.00")
        PrecioCliente.objects.create(producto=product, cliente=self.ajeno, precio="40.00")

        vendedor = self.login("vendedor")
        response = vendedor.get(f"/api/productos/{product.id}/")
        self.assertEqual(response.status_code, 200)
        nombres = [price["cliente_nombre"] for price in response.data["precios"]]
        self.assertEqual(nombres, ["Pulpería de la ruta"])

        contador = self.login("contador")
        listed = contador.get("/api/productos/")
        self.assertEqual(listed.status_code, 200)
        self.assertGreaterEqual(listed.data["count"], 1)
        forbidden = contador.post(
            "/api/productos/",
            {"nombre": "No", "unidad": "unidad", "precio_base": "1"},
            format="json",
        )
        self.assertEqual(forbidden.status_code, 403)
