from django.db import models


class UnidadMedida(models.TextChoices):
    UNIDAD = "unidad", "Unidad"
    LIBRA = "libra", "Libra"


class Producto(models.Model):
    codigo = models.CharField("código", max_length=20, unique=True, blank=True)
    nombre = models.CharField("nombre", max_length=160)
    unidad = models.CharField("unidad", max_length=16, choices=UnidadMedida.choices)
    precio_base = models.DecimalField("precio de lista", max_digits=12, decimal_places=2, default=0)
    controla_lote = models.BooleanField("lleva lote y vencimiento", default=False)
    activo = models.BooleanField("activo", default=True)
    notas = models.TextField("notas", blank=True)
    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "producto"
        verbose_name_plural = "productos"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.codigo:
            self.codigo = f"PR-{self.pk:05d}"
            super().save(update_fields=["codigo"])

    def precio_para(self, cliente):
        acuerdo = self.precios.filter(cliente=cliente).first()
        if acuerdo is not None:
            return acuerdo.precio
        return self.precio_base


class PrecioCliente(models.Model):
    producto = models.ForeignKey(Producto, related_name="precios", on_delete=models.CASCADE)
    cliente = models.ForeignKey("clientes.Cliente", related_name="precios", on_delete=models.PROTECT)
    precio = models.DecimalField("precio", max_digits=12, decimal_places=2)
    actualizado_en = models.DateTimeField("actualizado en", auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["producto", "cliente"], name="precio_producto_cliente"),
        ]
        ordering = ["cliente__nombre"]
        verbose_name = "precio por cliente"
        verbose_name_plural = "precios por cliente"

    def __str__(self):
        return f"{self.producto} · {self.cliente}"
