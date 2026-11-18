from django.db import models


class EmpresaFiscal(models.Model):
    razon_social = models.CharField(max_length=200)
    nombre = models.CharField(max_length=200, blank=True)
    desde = models.DateField(null=True, blank=True)
    hasta = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "empresa fiscal"
        verbose_name_plural = "empresa fiscal"

    def __str__(self):
        return self.razon_social


class DocumentoVenta(models.Model):
    registro = models.PositiveIntegerField(unique=True)
    fecha = models.DateField(db_index=True)
    caja = models.CharField(max_length=40, db_index=True)
    tipo = models.CharField(max_length=40)
    serie = models.CharField(max_length=20)
    numero = models.CharField(max_length=20, db_index=True)
    cai = models.CharField(max_length=120, blank=True)
    fecha_limite = models.DateField(null=True, blank=True)
    rtn = models.CharField(max_length=20, blank=True, db_index=True)
    cliente = models.CharField(max_length=255, db_index=True)
    condicion = models.CharField(max_length=20, db_index=True)
    forma_pago = models.CharField(max_length=20)
    moneda = models.CharField(max_length=8, default="HNL")
    exenta = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    exonerada = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gravada_15 = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    isv_15 = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gravada_18 = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    isv_18 = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, db_index=True)

    class Meta:
        ordering = ["-fecha", "-registro"]
        constraints = [
            models.UniqueConstraint(fields=["serie", "numero"], name="documento_serie_numero"),
        ]
        verbose_name = "documento de venta"
        verbose_name_plural = "documentos de venta"

    def __str__(self):
        return f"{self.serie}-{self.numero}"


class Proveedor(models.Model):
    nombre = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "proveedores"

    def __str__(self):
        return self.nombre


class CompraMensual(models.Model):
    proveedor = models.ForeignKey(Proveedor, related_name="compras", on_delete=models.CASCADE)
    anio = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField()
    monto = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["proveedor", "anio", "mes"], name="compra_proveedor_mes"),
        ]
        ordering = ["proveedor__nombre", "anio", "mes"]


class VendedorReporte(models.Model):
    nombre = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "vendedor del reporte"
        verbose_name_plural = "vendedores del reporte"

    def __str__(self):
        return self.nombre


class VentaMensual(models.Model):
    vendedor = models.ForeignKey(VendedorReporte, related_name="ventas", on_delete=models.CASCADE)
    anio = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField()
    monto = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["vendedor", "anio", "mes"], name="venta_vendedor_mes"),
        ]
        ordering = ["vendedor__nombre", "anio", "mes"]


class CierreDiario(models.Model):
    fecha = models.DateField(unique=True)
    numero = models.PositiveIntegerField(null=True, blank=True)
    factura_desde = models.CharField(max_length=20, blank=True)
    factura_hasta = models.CharField(max_length=20, blank=True)
    concepto = models.CharField(max_length=120)
    venta_libre = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    venta_gravada = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ["fecha"]
        verbose_name = "cierre diario"
        verbose_name_plural = "cierres diarios"

    def __str__(self):
        return self.concepto
