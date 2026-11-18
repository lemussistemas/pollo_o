from django.conf import settings
from django.db import models


class TipoVehiculo(models.TextChoices):
    CAMION = "camion", "Camión"
    MOTOCARGA = "motocarga", "Motocarga"


class Vehiculo(models.Model):
    codigo = models.CharField("código", max_length=32, unique=True)
    nombre = models.CharField("nombre", max_length=80)
    tipo = models.CharField("tipo", max_length=16, choices=TipoVehiculo.choices)
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="vendedor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vehiculos",
    )
    activo = models.BooleanField("activo", default=True)

    class Meta:
        ordering = ["codigo"]
        verbose_name = "vehículo"
        verbose_name_plural = "vehículos"

    def __str__(self):
        return self.nombre


class Carga(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, related_name="cargas", on_delete=models.PROTECT)
    fecha = models.DateField("fecha")
    nota = models.CharField("nota", max_length=200, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cargas_armadas",
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["vehiculo", "fecha"], name="carga_vehiculo_fecha"),
        ]
        ordering = ["-fecha", "vehiculo__codigo"]
        verbose_name = "carga"
        verbose_name_plural = "cargas"

    def __str__(self):
        return f"{self.vehiculo} {self.fecha}"


class CargaLinea(models.Model):
    carga = models.ForeignKey(Carga, related_name="lineas", on_delete=models.CASCADE)
    producto = models.ForeignKey("productos.Producto", on_delete=models.PROTECT)
    lote = models.CharField("lote", max_length=40, blank=True)
    fecha_vencimiento = models.DateField("vencimiento", null=True, blank=True)
    cantidad = models.DecimalField("cantidad", max_digits=14, decimal_places=3)
    creado_en = models.DateTimeField("creado en", auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "línea de carga"
        verbose_name_plural = "líneas de carga"
