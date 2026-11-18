from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.seed import DEMO_PASSWORD, seed
from bodega.models import Existencia
from distribucion.models import Vehiculo


class CargaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()

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

    def receive(self, client, product_id, quantity, lot="", expiration=None):
        body = {"tipo": "ingreso", "producto_id": product_id, "cantidad": quantity}
        if lot:
            body["lote"] = lot
            body["fecha_vencimiento"] = expiration
        response = client.post("/api/bodega/movimientos/", body, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        return response

    def test_loading_a_truck_reduces_warehouse_stock(self):
        from productos.models import Producto

        inventario = self.login("inventario")
        product = Producto.objects.create(nombre="Alitas carga", unidad="libra", controla_lote=True)
        tomorrow = (timezone.localdate() + timedelta(days=4)).isoformat()
        self.receive(inventario, product.id, "10", "L-9", tomorrow)
        stock = Existencia.objects.get(producto=product)
        truck = Vehiculo.objects.get(codigo="camion-1")
        today = timezone.localdate().isoformat()

        opened = inventario.post(
            "/api/distribucion/cargas/",
            {"vehiculo_id": truck.id, "fecha": today},
            format="json",
        )
        self.assertEqual(opened.status_code, 201, opened.content)
        loaded = inventario.post(
            f"/api/distribucion/cargas/{opened.data['id']}/lineas/",
            {"existencia_id": stock.id, "cantidad": "4"},
            format="json",
        )
        self.assertEqual(loaded.status_code, 201, loaded.content)
        self.assertEqual(loaded.data["lineas"][0]["lote"], "L-9")
        self.assertEqual(Decimal(loaded.data["lineas"][0]["cantidad"]), Decimal("4"))
        stock.refresh_from_db()
        self.assertEqual(stock.cantidad, Decimal("6"))

        too_much = inventario.post(
            f"/api/distribucion/cargas/{opened.data['id']}/lineas/",
            {"existencia_id": stock.id, "cantidad": "9"},
            format="json",
        )
        self.assertEqual(too_much.status_code, 400)
        stock.refresh_from_db()
        self.assertEqual(stock.cantidad, Decimal("6"))

        fleet = inventario.get("/api/distribucion/vehiculos/")
        self.assertEqual(len(fleet.data["vehiculos"]), 4)

    def test_seller_sees_only_his_vehicle_and_cannot_load_it(self):
        inventario = self.login("inventario")
        truck = Vehiculo.objects.get(codigo="camion-1")
        other = Vehiculo.objects.get(codigo="motocarga")
        from django.contrib.auth import get_user_model

        seller = get_user_model().objects.get(username="vendedor")
        assigned = inventario.patch(f"/api/distribucion/vehiculos/{truck.id}/", {"vendedor_id": seller.id}, format="json")
        self.assertEqual(assigned.status_code, 200, assigned.content)
        today = timezone.localdate().isoformat()
        inventario.post("/api/distribucion/cargas/", {"vehiculo_id": truck.id, "fecha": today}, format="json")

        vendedor = self.login("vendedor")
        own = vendedor.get("/api/distribucion/vehiculos/")
        self.assertEqual([item["codigo"] for item in own.data["vehiculos"]], ["camion-1"])
        seen = vendedor.get("/api/distribucion/cargas/", {"vehiculo": truck.id, "fecha": today})
        self.assertEqual(seen.status_code, 200)
        self.assertEqual(len(seen.data), 1)
        hidden = vendedor.get("/api/distribucion/cargas/", {"vehiculo": other.id})
        self.assertEqual(hidden.data, [])
        denied = vendedor.post("/api/distribucion/cargas/", {"vehiculo_id": truck.id, "fecha": today}, format="json")
        self.assertEqual(denied.status_code, 403)

        contador = self.login("contador")
        listed = contador.get("/api/distribucion/vehiculos/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data["vehiculos"]), 4)
        blocked = contador.post("/api/distribucion/cargas/", {"vehiculo_id": truck.id, "fecha": today}, format="json")
        self.assertEqual(blocked.status_code, 403)

        facturacion = self.login("facturacion")
        self.assertEqual(facturacion.get("/api/distribucion/vehiculos/").status_code, 403)
