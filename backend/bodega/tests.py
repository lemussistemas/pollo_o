from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.seed import DEMO_PASSWORD, seed
from productos.models import Producto


class BodegaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.alitas = Producto.objects.create(nombre="Alitas", unidad="libra", precio_base="42.00", controla_lote=True)
        cls.huevo = Producto.objects.create(nombre="Huevo", unidad="unidad", precio_base="5.00", controla_lote=False)

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

    def test_ingreso_requires_lot_and_updates_stock(self):
        inventario = self.login("inventario")
        missing = inventario.post(
            "/api/bodega/movimientos/",
            {"tipo": "ingreso", "producto_id": self.alitas.id, "cantidad": "10"},
            format="json",
        )
        self.assertEqual(missing.status_code, 400)
        self.assertIn("lote", missing.data)

        tomorrow = (timezone.localdate() + timedelta(days=5)).isoformat()
        created = inventario.post(
            "/api/bodega/movimientos/",
            {
                "tipo": "ingreso",
                "producto_id": self.alitas.id,
                "cantidad": "12.5",
                "lote": "L-1",
                "fecha_vencimiento": tomorrow,
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.content)
        stock = inventario.get("/api/bodega/existencias/")
        self.assertEqual(stock.status_code, 200)
        row = stock.data[0]
        self.assertEqual(row["lote"], "L-1")
        self.assertEqual(Decimal(row["cantidad"]), Decimal("12.5"))

        extra = inventario.post(
            "/api/bodega/movimientos/",
            {
                "tipo": "salida_danado",
                "producto_id": self.alitas.id,
                "cantidad": "2.5",
                "lote": "L-1",
                "fecha_vencimiento": tomorrow,
                "nota": "Se descongeló",
            },
            format="json",
        )
        self.assertEqual(extra.status_code, 201, extra.content)
        stock = inventario.get("/api/bodega/existencias/")
        self.assertEqual(Decimal(stock.data[0]["cantidad"]), Decimal("10"))

        too_much = inventario.post(
            "/api/bodega/movimientos/",
            {
                "tipo": "salida_danado",
                "producto_id": self.alitas.id,
                "cantidad": "40",
                "lote": "L-1",
                "fecha_vencimiento": tomorrow,
            },
            format="json",
        )
        self.assertEqual(too_much.status_code, 400)
        stock = inventario.get("/api/bodega/existencias/")
        self.assertEqual(Decimal(stock.data[0]["cantidad"]), Decimal("10"))

    def test_plain_product_rejects_a_lot_and_other_roles_cannot_receive(self):
        inventario = self.login("inventario")
        rejected = inventario.post(
            "/api/bodega/movimientos/",
            {"tipo": "ingreso", "producto_id": self.huevo.id, "cantidad": "4", "lote": "X"},
            format="json",
        )
        self.assertEqual(rejected.status_code, 400)
        accepted = inventario.post(
            "/api/bodega/movimientos/",
            {"tipo": "ingreso", "producto_id": self.huevo.id, "cantidad": "4"},
            format="json",
        )
        self.assertEqual(accepted.status_code, 201, accepted.content)

        facturacion = self.login("facturacion")
        denied = facturacion.post(
            "/api/bodega/movimientos/",
            {"tipo": "ingreso", "producto_id": self.huevo.id, "cantidad": "1"},
            format="json",
        )
        self.assertEqual(denied.status_code, 403)
        hidden = facturacion.get("/api/bodega/existencias/")
        self.assertEqual(hidden.status_code, 403)

        contador = self.login("contador")
        visible = contador.get("/api/bodega/movimientos/")
        self.assertEqual(visible.status_code, 200)
        self.assertGreaterEqual(visible.data["count"], 1)
        blocked = contador.post(
            "/api/bodega/movimientos/",
            {"tipo": "ingreso", "producto_id": self.huevo.id, "cantidad": "1"},
            format="json",
        )
        self.assertEqual(blocked.status_code, 403)
