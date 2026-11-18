from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class AccessLevel(models.TextChoices):
    NONE = "none", "Sin acceso"
    VIEW = "view", "Consulta"
    OWN = "own", "Solo lo propio"
    OPERATE = "operate", "Operar"
    FULL = "full", "Completo"


LEVEL_RANK = {
    AccessLevel.NONE: 0,
    AccessLevel.VIEW: 1,
    AccessLevel.OWN: 2,
    AccessLevel.OPERATE: 3,
    AccessLevel.FULL: 4,
}


class RoleCode(models.TextChoices):
    GERENCIA = "gerencia", "Admin"
    CONTADOR = "contador", "Contabilidad"
    FACTURACION = "facturacion", "Facturación"
    VENDEDOR = "vendedor", "Vendedor"
    INVENTARIO = "inventario", "Inventario"


class UserManager(DjangoUserManager):
    def with_access(self):
        return self.select_related("role").prefetch_related("role__grants__permission")


class Role(models.Model):
    code = models.CharField("código", max_length=32, unique=True, choices=RoleCode.choices)
    name = models.CharField("nombre", max_length=64)
    summary = models.CharField("resumen", max_length=255)
    description = models.TextField("descripción")
    sort_order = models.PositiveSmallIntegerField("orden", default=0)
    is_system = models.BooleanField("rol del sistema", default=True)

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "roles"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Permission(models.Model):
    code = models.CharField("código", max_length=64, unique=True)
    module = models.CharField("módulo", max_length=32)
    name = models.CharField("nombre", max_length=128)
    description = models.TextField("descripción", blank=True)
    sort_order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "permiso"
        verbose_name_plural = "permisos"
        ordering = ["sort_order", "code"]

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, related_name="grants", on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, related_name="grants", on_delete=models.CASCADE)
    level = models.CharField(
        "nivel",
        max_length=16,
        choices=AccessLevel.choices,
        default=AccessLevel.NONE,
    )

    class Meta:
        verbose_name = "permiso del rol"
        verbose_name_plural = "permisos del rol"
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="unique_role_permission")
        ]

    def __str__(self):
        return f"{self.role.code}:{self.permission.code}:{self.level}"


class User(AbstractUser):
    role = models.ForeignKey(
        Role,
        verbose_name="rol",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users",
    )
    phone = models.CharField("teléfono", max_length=32, blank=True)

    objects = UserManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["first_name", "last_name", "username"]

    def access_map(self):
        cached = getattr(self, "_access_map", None)
        if cached is not None:
            return cached
        mapping = {}
        if self.role_id:
            for grant in self.role.grants.all():
                mapping[grant.permission.code] = grant.level
        self._access_map = mapping
        return mapping

    def has_access(self, code, minimum=AccessLevel.VIEW):
        if minimum not in LEVEL_RANK:
            raise ValueError(f"Nivel desconocido: {minimum}")
        if not self.is_active:
            return False
        current = self.access_map().get(code, AccessLevel.NONE)
        return LEVEL_RANK[current] >= LEVEL_RANK[minimum]
