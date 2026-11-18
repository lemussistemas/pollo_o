from django.conf import settings
from django.db import models
from django.utils import timezone


class PuntoVenta(models.Model):
    code = models.CharField("código", max_length=32, unique=True)
    name = models.CharField("nombre", max_length=80)
    sort_order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "punto de venta"
        verbose_name_plural = "puntos de venta"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class DiaRuta(models.TextChoices):
    LUNES = "lunes", "Lunes"
    MARTES = "martes", "Martes"
    MIERCOLES = "miercoles", "Miércoles"
    JUEVES = "jueves", "Jueves"
    VIERNES = "viernes", "Viernes"
    SABADO = "sabado", "Sábado"
    DOMINGO = "domingo", "Domingo"


class Cliente(models.Model):
    codigo = models.CharField("código", max_length=20, unique=True, blank=True)
    nombre = models.CharField("nombre", max_length=160)
    rtn = models.CharField("RTN", max_length=20, blank=True)
    telefono = models.CharField("teléfono", max_length=32, blank=True)
    direccion = models.CharField("dirección", max_length=255, blank=True)
    punto = models.ForeignKey(PuntoVenta, verbose_name="punto de venta", on_delete=models.PROTECT, related_name="clientes")
    dia_ruta = models.CharField("día de ruta", max_length=16, blank=True, choices=DiaRuta.choices)
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="vendedor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clientes_ruta",
    )
    latitud = models.DecimalField("latitud", max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField("longitud", max_digits=9, decimal_places=6, null=True, blank=True)
    credito_habilitado = models.BooleanField("crédito autorizado", default=False)
    limite_credito = models.DecimalField("límite de crédito", max_digits=12, decimal_places=2, null=True, blank=True)
    credito_autorizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="crédito autorizado por",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="creditos_autorizados",
    )
    credito_autorizado_en = models.DateTimeField("crédito autorizado en", null=True, blank=True)
    notas = models.TextField("notas", blank=True)
    activo = models.BooleanField("activo", default=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="creado por",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clientes_creados",
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.codigo:
            self.codigo = f"CL-{self.pk:05d}"
            super().save(update_fields=["codigo"])


class EstadoEquipo(models.TextChoices):
    INSTALADO = "instalado", "Instalado"
    RETIRADO = "retirado", "Retirado"


class Equipo(models.Model):
    cliente = models.ForeignKey(Cliente, related_name="equipos", on_delete=models.CASCADE)
    modelo = models.CharField("modelo", max_length=120)
    placa = models.CharField("placa", max_length=32, blank=True)
    foto = models.ImageField("foto", upload_to="equipos/%Y/%m/", blank=True)
    ubicacion = models.CharField("ubicación", max_length=160, blank=True)
    latitud = models.DecimalField("latitud", max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField("longitud", max_digits=9, decimal_places=6, null=True, blank=True)
    estado = models.CharField(
        "estado",
        max_length=16,
        choices=EstadoEquipo.choices,
        default=EstadoEquipo.INSTALADO,
    )
    ubicacion_bloqueada = models.BooleanField("ubicación cerrada", default=False)
    retirado_en = models.DateTimeField("retirado en", null=True, blank=True)

    class Meta:
        verbose_name = "equipo"
        verbose_name_plural = "equipos"
        ordering = ["id"]

    def __str__(self):
        return self.modelo

    def save(self, *args, **kwargs):
        if self.estado == EstadoEquipo.RETIRADO:
            self.ubicacion_bloqueada = True
            if self.retirado_en is None:
                self.retirado_en = timezone.now()
        else:
            self.ubicacion_bloqueada = False
            self.retirado_en = None
        super().save(*args, **kwargs)
