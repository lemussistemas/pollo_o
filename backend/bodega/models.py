from django.conf import settings
from django.db import models


class TipoMovimiento(models.TextChoices):
    INGRESO = "ingreso", "Ingreso"
    SALIDA_DANADO = "salida_danado", "Salida por dañado"
    CARGA = "carga", "Carga a vehículo"


def clave_de(lote, fecha):
    limpio = (lote or "").strip()
    dia = fecha.isoformat() if fecha else ""
    return f"{limpio}|{dia}"


class Existencia(models.Model):
    producto = models.ForeignKey("productos.Producto", related_name="existencias", on_delete=models.PROTECT)
    lote = models.CharField("lote", max_length=40, blank=True)
    fecha_vencimiento = models.DateField("vencimiento", null=True, blank=True)
    clave = models.CharField(max_length=80)
    cantidad = models.DecimalField("cantidad", max_digits=14, decimal_places=3, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["producto", "clave"], name="existencia_producto_lote"),
        ]
        ordering = ["producto__nombre", "fecha_vencimiento", "lote"]
        verbose_name = "existencia"
        verbose_name_plural = "existencias"

    def __str__(self):
        return f"{self.producto} {self.cantidad}"

    def save(self, *args, **kwargs):
        self.lote = (self.lote or "").strip()
        self.clave = clave_de(self.lote, self.fecha_vencimiento)
        super().save(*args, **kwargs)


class Movimiento(models.Model):
    tipo = models.CharField("tipo", max_length=20, choices=TipoMovimiento.choices)
    producto = models.ForeignKey("productos.Producto", related_name="movimientos", on_delete=models.PROTECT)
    lote = models.CharField("lote", max_length=40, blank=True)
    fecha_vencimiento = models.DateField("vencimiento", null=True, blank=True)
    cantidad = models.DecimalField("cantidad", max_digits=14, decimal_places=3)
    nota = models.CharField("nota", max_length=200, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="movimientos_bodega",
    )
    creado_en = models.DateTimeField("creado en", auto_now_add=True)

    class Meta:
        ordering = ["-creado_en", "-id"]
        verbose_name = "movimiento"
        verbose_name_plural = "movimientos"

    def __str__(self):
        return f"{self.get_tipo_display()} {self.producto}"

    def save(self, *args, **kwargs):
        self.lote = (self.lote or "").strip()
        super().save(*args, **kwargs)
