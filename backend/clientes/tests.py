import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient

from accounts.models import User
from accounts.seed import DEMO_PASSWORD, seed

from .models import Equipo, PuntoVenta


def tiny_png():
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, format="PNG")
    return SimpleUploadedFile("equipo.png", buffer.getvalue(), content_type="image/png")


class ClienteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        cls.punto = PuntoVenta.objects.get(code="pulperias")

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

    def payload(self, **extra):
        data = {
            "nombre": "Pulpería El Parque",
            "rtn": "08011990123456",
            "telefono": "99990000",
            "direccion": "Suyapa",
            "punto_id": self.punto.pk,
            "dia_ruta": "lunes",
            "latitud": "14.090000",
            "longitud": "-87.190000",
        }
        data.update(extra)
        return data

    def test_facturacion_creates_client_without_credit(self):
        client = self.login("facturacion")
        created = client.post("/api/clientes/", self.payload(), format="json")
        self.assertEqual(created.status_code, 201, created.content)
        self.assertFalse(created.data["credito_habilitado"])
        self.assertTrue(created.data["es_nuevo"])
        self.assertEqual(created.data["punto"]["code"], "pulperias")

        denied = client.patch(
            f"/api/clientes/{created.data['id']}/",
            {"credito_habilitado": True, "limite_credito": "1500.00"},
            format="json",
        )
        self.assertEqual(denied.status_code, 400, denied.content)
        self.assertIn("gerencia", str(denied.data).lower())

    def test_gerencia_authorizes_credit_with_a_limit(self):
        client = self.login("gerencia")
        created = client.post(
            "/api/clientes/",
            self.payload(nombre="Abarrotería Central", credito_habilitado=True),
            format="json",
        )
        self.assertEqual(created.status_code, 400, created.content)

        created = client.post(
            "/api/clientes/",
            self.payload(
                nombre="Abarrotería Central",
                credito_habilitado=True,
                limite_credito="2500.00",
            ),
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.content)
        self.assertTrue(created.data["credito_habilitado"])
        self.assertEqual(created.data["limite_credito"], "2500.00")
        self.assertEqual(created.data["credito_autorizado_por"]["id"], User.objects.get(username="gerencia").pk)

    def test_vendedor_only_sees_assigned_clients(self):
        manager = self.login("facturacion")
        seller = User.objects.get(username="vendedor")
        own = manager.post("/api/clientes/", self.payload(vendedor_id=seller.pk), format="json")
        other = manager.post("/api/clientes/", self.payload(nombre="Otro cliente"), format="json")
        self.assertEqual(own.status_code, 201, own.content)
        self.assertEqual(other.status_code, 201, other.content)

        route = self.login("vendedor")
        listing = route.get("/api/clientes/")
        self.assertEqual(listing.status_code, 200, listing.content)
        names = [item["nombre"] for item in listing.data["results"]]
        self.assertIn("Pulpería El Parque", names)
        self.assertNotIn("Otro cliente", names)
        hidden = route.get(f"/api/clientes/{other.data['id']}/")
        self.assertEqual(hidden.status_code, 404)

    def test_withdrawn_equipment_locks_its_location(self):
        client = self.login("facturacion")
        created = client.post("/api/clientes/", self.payload(nombre="Cliente con equipo"), format="json")
        cliente_id = created.data["id"]
        equipo = client.post(
            f"/api/clientes/{cliente_id}/equipos/",
            {"modelo": "Congelador 1", "placa": "AB1234", "ubicacion": "Suyapa", "foto": tiny_png()},
            format="multipart",
        )
        self.assertEqual(equipo.status_code, 201, equipo.content)
        self.assertTrue(equipo.data["foto"].endswith(".png"))

        withdrawn = client.patch(
            f"/api/clientes/{cliente_id}/equipos/{equipo.data['id']}/",
            {"estado": "retirado"},
            format="json",
        )
        self.assertEqual(withdrawn.status_code, 200, withdrawn.content)
        self.assertTrue(withdrawn.data["ubicacion_bloqueada"])
        self.assertEqual(withdrawn.data["ubicacion"], "Suyapa")

        moved = client.patch(
            f"/api/clientes/{cliente_id}/equipos/{equipo.data['id']}/",
            {"ubicacion": "Otra colonia"},
            format="json",
        )
        self.assertEqual(moved.status_code, 400, moved.content)
        self.assertEqual(Equipo.objects.get(pk=equipo.data["id"]).ubicacion, "Suyapa")

    def test_contador_can_read_clients_but_not_create_them(self):
        self.login("facturacion").post("/api/clientes/", self.payload(), format="json")
        contador = self.login("contador")
        listing = contador.get("/api/clientes/")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.data["count"], 1)
        denied = contador.post("/api/clientes/", self.payload(nombre="No debe"), format="json")
        self.assertEqual(denied.status_code, 403)
