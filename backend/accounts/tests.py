from django.test import TestCase
from rest_framework.test import APIClient

from .models import AccessLevel, Role, RolePermission, User
from .seed import DEMO_PASSWORD, seed


class RoleSetupTests(TestCase):
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
        return client, response.data["user"]

    def test_catalog_has_five_roles_and_full_matrix(self):
        self.assertEqual(Role.objects.count(), 5)
        self.assertEqual(RolePermission.objects.count(), 5 * 23)
        gerencia = RolePermission.objects.get(
            role__code="gerencia", permission__code="usuarios.gestionar"
        )
        self.assertEqual(gerencia.level, AccessLevel.FULL)
        vendedor = User.objects.get(username="vendedor")
        self.assertTrue(vendedor.has_access("facturacion.ruta", AccessLevel.OWN))
        self.assertFalse(vendedor.has_access("facturacion.ruta", AccessLevel.OPERATE))
        self.assertFalse(vendedor.has_access("usuarios.gestionar", AccessLevel.VIEW))
        inventario = User.objects.get(username="inventario")
        self.assertTrue(inventario.has_access("inventario.ingreso", AccessLevel.OPERATE))
        self.assertTrue(inventario.has_access("inventario.mal_estado", AccessLevel.OPERATE))
        self.assertFalse(inventario.has_access("facturacion.pdv", AccessLevel.OPERATE))
        facturacion = User.objects.get(username="facturacion")
        self.assertTrue(facturacion.has_access("facturacion.pdv", AccessLevel.OPERATE))
        self.assertTrue(facturacion.has_access("cierre.pdv", AccessLevel.OPERATE))
        self.assertFalse(facturacion.has_access("cierre.vendedor", AccessLevel.OPERATE))
        contador = User.objects.get(username="contador")
        self.assertTrue(contador.has_access("cierre.contable", AccessLevel.FULL))
        self.assertFalse(contador.has_access("usuarios.gestionar", AccessLevel.VIEW))

    def test_login_rejects_bad_password_and_inactive_user(self):
        client = APIClient()
        bad = client.post(
            "/api/auth/login/",
            {"username": "vendedor", "password": "no-es-la-clave"},
            format="json",
        )
        self.assertEqual(bad.status_code, 401)

        user = User.objects.get(username="vendedor")
        user.is_active = False
        user.save(update_fields=["is_active"])
        inactive = client.post(
            "/api/auth/login/",
            {"username": "vendedor", "password": DEMO_PASSWORD},
            format="json",
        )
        self.assertEqual(inactive.status_code, 401)

    def test_vendedor_sees_only_his_part_of_the_day(self):
        client, _user = self.login("vendedor")
        response = client.get("/api/sistema/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["puntos_de_venta"], 5)
        self.assertEqual(
            [point["name"] for point in response.data["puntos"]],
            ["Ruta foránea", "Pulperías", "Bodegas", "Sala de ventas", "OPL"],
        )
        self.assertEqual(response.data["vehiculos"], {"camiones": 3, "motocarga": 1})
        steps = {step["code"]: step for step in response.data["flujo"]}
        self.assertEqual(steps["facturacion_ruta"]["nivel"], "own")
        self.assertFalse(steps["facturacion_pdv"]["participa"])
        self.assertFalse(steps["cuadre"]["participa"])
        self.assertTrue(steps["regreso"]["participa"])
        self.assertEqual(steps["cierre_vendedor"]["nivel"], "own")

    def test_vendedor_cannot_create_users_and_gerencia_can(self):
        vendedor, _user = self.login("vendedor")
        denied = vendedor.post(
            "/api/usuarios/",
            {
                "username": "ruta2",
                "password": "Clave-segura-1",
                "first_name": "Ruta",
                "last_name": "Dos",
                "role_id": Role.objects.get(code="vendedor").pk,
            },
            format="json",
        )
        self.assertEqual(denied.status_code, 403)

        gerencia, _actor = self.login("gerencia")
        created = gerencia.post(
            "/api/usuarios/",
            {
                "username": "ruta2",
                "password": "Clave-segura-1",
                "first_name": "Ruta",
                "last_name": "Dos",
                "phone": "55551212",
                "role_id": Role.objects.get(code="vendedor").pk,
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.content)
        self.assertEqual(created.data["role"]["code"], "vendedor")
        self.assertTrue(created.data["is_active"])

    def test_contador_can_read_users_but_not_change_them(self):
        contador, _user = self.login("contador")
        listing = contador.get("/api/usuarios/")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(len(listing.data), 5)
        role_id = Role.objects.get(code="inventario").pk
        target = User.objects.get(username="inventario")
        update = contador.patch(
            f"/api/usuarios/{target.pk}/",
            {"phone": "55550000", "role_id": role_id},
            format="json",
        )
        self.assertEqual(update.status_code, 403)

    def test_last_gerencia_cannot_be_removed(self):
        client, actor = self.login("gerencia")
        blocked = client.patch(
            f"/api/usuarios/{actor['id']}/",
            {"is_active": False},
            format="json",
        )
        self.assertEqual(blocked.status_code, 400, blocked.content)
        self.assertIn("admin", str(blocked.data).lower())

        other = client.post(
            "/api/usuarios/",
            {
                "username": "gerencia2",
                "password": "Clave-segura-1",
                "first_name": "Gerencia",
                "last_name": "Dos",
                "role_id": Role.objects.get(code="gerencia").pk,
            },
            format="json",
        )
        self.assertEqual(other.status_code, 201, other.content)
        demoted = client.patch(
            f"/api/usuarios/{actor['id']}/",
            {"role_id": Role.objects.get(code="contador").pk},
            format="json",
        )
        self.assertEqual(demoted.status_code, 200, demoted.content)
        self.assertEqual(demoted.data["role"]["code"], "contador")
