from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase
from openpyxl import Workbook
from rest_framework.test import APIClient

from accounts.seed import DEMO_PASSWORD, seed
from libros.excel_import import import_libros
from libros.models import DocumentoVenta


def _ventas(path):
    book = Workbook()
    sheet = book.active
    sheet["A4"] = "Razón social:"
    sheet["B4"] = "DEPOSITO OLANCHITO"
    sheet["C4"] = "Desde:"
    sheet["D4"] = datetime(2026, 1, 1)
    sheet["E4"] = "Hasta:"
    sheet["F4"] = datetime(2026, 11, 18)
    sheet["A5"] = "Dirección:"
    sheet["B5"] = "POLLO REY"
    headers = [
        "Registro", "Fecha", "Caja / POS", "Tipo documento", "Serie", "No. documento", "CAI",
        "Fecha límite emisión", "RTN / DNI cliente", "Nombre del cliente", "Condición venta",
        "Forma de pago", "Moneda", "Venta exenta", "Venta exonerada", "Venta gravada 15%",
        "ISV 15%", "Venta gravada 18%", "ISV 18%", "Descuento", "Total documento", "Estado",
    ]
    for column, header in enumerate(headers, start=1):
        sheet.cell(7, column, header)
    sheet.append([])
    sheet.cell(8, 1, 1)
    sheet.cell(8, 2, datetime(2026, 1, 2))
    sheet.cell(8, 3, "OFICINA")
    sheet.cell(8, 4, "TALONARIO")
    sheet.cell(8, 5, "000-002-01")
    sheet.cell(8, 6, "00030986")
    sheet.cell(8, 7, "545B89")
    sheet.cell(8, 8, datetime(2030, 2, 17))
    sheet.cell(8, 9, 18079023552377)
    sheet.cell(8, 10, "PULP. EMANUEL")
    sheet.cell(8, 11, "CREDITO")
    sheet.cell(8, 12, "CREDITO")
    sheet.cell(8, 13, "HNL")
    sheet.cell(8, 14, 1453.2)
    sheet.cell(8, 16, 143.48)
    sheet.cell(8, 17, 21.52)
    sheet.cell(8, 21, 1618.2)
    sheet.cell(8, 22, "VIGENTE")
    sheet.cell(9, 1, 2)
    sheet.cell(9, 2, datetime(2026, 1, 5))
    sheet.cell(9, 3, "CAJA")
    sheet.cell(9, 4, "FACTURA")
    sheet.cell(9, 5, "000-001-01")
    sheet.cell(9, 6, 337893)
    sheet.cell(9, 10, "ANULADO EJEMPLO")
    sheet.cell(9, 11, "CONTADO")
    sheet.cell(9, 12, "EFECTIVO")
    sheet.cell(9, 13, "HNL")
    sheet.cell(9, 22, "ANULADO")
    book.save(path)


def _months(path, title, header, name, january):
    book = Workbook()
    sheet = book.active
    sheet["A3"] = title
    sheet["A6"] = header
    for column, month in enumerate(["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC", "TOT"], start=2):
        sheet.cell(6, column, month)
    sheet["A7"] = name
    sheet["B7"] = january
    sheet["A8"] = ":::Totales:::"
    sheet["B8"] = january
    book.save(path)


def _cierres(path):
    book = Workbook()
    sheet = book.active
    sheet["A5"] = "FECHA"
    sheet["B5"] = "CONCEPTO"
    sheet["C5"] = "VTS LIBRE"
    sheet["D5"] = "VTS GRABADA"
    sheet["E5"] = "IMPUESTO"
    sheet["F5"] = "VTS TOTAL"
    sheet["A6"] = "10/1/2026"
    sheet["B6"] = "Cierre# 2730 Fact: 355964-356020"
    sheet["C6"] = 42523.35
    sheet["D6"] = 2293.04
    sheet["E6"] = 343.96
    sheet["F6"] = 45160.35
    book.save(path)


class LibroImportTests(TestCase):
    def test_import_replaces_books_and_skips_totals(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            ventas = root / "ventas.xlsx"
            proveedores = root / "proveedores.xlsx"
            vendedores = root / "vendedores.xlsx"
            cierres = root / "cierres.xlsx"
            _ventas(ventas)
            _months(proveedores, "INFORME VENTAS POR Compras por Proveedor  AÑO: 2026", "Compras por Proveedor", "CADECA", 100)
            _months(vendedores, "INFORME VENTAS POR Vendedores  AÑO: 2026", "Vendedores", "02-CAMION", 50)
            _cierres(cierres)
            result = import_libros(
                ventas=ventas,
                proveedores=proveedores,
                vendedores=vendedores,
                cierres=cierres,
            )
        self.assertEqual(result, {"documentos": 2, "proveedores": 1, "vendedores": 1, "cierres": 1})
        credit = DocumentoVenta.objects.get(cliente="PULP. EMANUEL")
        self.assertEqual(str(credit.total), "1618.20")
        self.assertEqual(credit.rtn, "18079023552377")
        self.assertEqual(credit.numero, "00030986")
        voided = DocumentoVenta.objects.get(estado="ANULADO")
        self.assertEqual(voided.numero, "00337893")
        self.assertEqual(voided.fecha.isoformat(), "2026-01-05")
        from libros.models import CierreDiario, Proveedor, VendedorReporte

        self.assertEqual(CierreDiario.objects.get().fecha.isoformat(), "2026-10-01")
        self.assertEqual(CierreDiario.objects.get().numero, 2730)
        self.assertEqual(Proveedor.objects.get().compras.get(mes=1).monto, 100)
        self.assertEqual(Proveedor.objects.get().compras.count(), 12)
        self.assertEqual(VendedorReporte.objects.get().nombre, "02-CAMION")


class LibroApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed()
        with TemporaryDirectory() as folder:
            path = Path(folder) / "ventas.xlsx"
            _ventas(path)
            import_libros(ventas=path)

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

    def test_contador_reads_the_sales_book_and_vendedor_cannot(self):
        blocked = self.login("vendedor")
        denied = blocked.get("/api/libros/resumen/")
        self.assertEqual(denied.status_code, 403)

        client = self.login("contador")
        summary = client.get("/api/libros/resumen/")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.data["razon_social"], "DEPOSITO OLANCHITO")
        self.assertEqual(summary.data["documentos"], 2)
        self.assertEqual(summary.data["vigentes"], 1)
        self.assertEqual(summary.data["anulados"], 1)
        self.assertEqual(summary.data["ventas_netas"], "1618.20")
        self.assertEqual(summary.data["credito"]["documentos"], 1)

        documents = client.get("/api/libros/documentos/", {"q": "emanuel", "condicion": "CREDITO"})
        self.assertEqual(documents.status_code, 200)
        self.assertEqual(documents.data["count"], 1)
        self.assertEqual(documents.data["results"][0]["numero"], "00030986")

        facturacion = self.login("facturacion")
        visible = facturacion.get("/api/libros/documentos/")
        self.assertEqual(visible.status_code, 200)
        self.assertEqual(visible.data["count"], 2)
