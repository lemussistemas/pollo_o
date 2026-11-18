import re
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from openpyxl import load_workbook

from .models import (
    CierreDiario,
    CompraMensual,
    DocumentoVenta,
    EmpresaFiscal,
    Proveedor,
    VendedorReporte,
    VentaMensual,
)

CENT = Decimal("0.01")
CIERRE_RE = re.compile(r"Cierre#\s*(\d+)\s*Fact:\s*(\d+)\s*-\s*(\d+)", re.IGNORECASE)
YEAR_RE = re.compile(r"AÑO:\s*(\d{4})", re.IGNORECASE)


def money(value):
    if value is None or value == "":
        return Decimal("0.00")
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None or value == "":
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:19] if " " in text and "-" in text else text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"No se pudo leer la fecha {value!r}.")


def text_id(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value).strip()


def document_number(value):
    raw = text_id(value)
    if raw.isdigit() and len(raw) < 8:
        return raw.zfill(8)
    return raw


def _rows(path):
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook[workbook.sheetnames[0]]
    rows = list(sheet.iter_rows(values_only=True))
    workbook.close()
    return rows


def _cell(row, index):
    if row is None or index >= len(row):
        return None
    return row[index]


def _find_row(rows, label, column=0):
    target = label.strip().lower()
    for index, row in enumerate(rows):
        value = _cell(row, column)
        if value is not None and str(value).strip().lower() == target:
            return index
    raise ValueError(f"No encontré la fila {label!r}.")


def _year_from(rows, default):
    for row in rows[:8]:
        for cell in row:
            if cell is None:
                continue
            match = YEAR_RE.search(str(cell))
            if match:
                return int(match.group(1))
    return default


def _store_months(model, fk_name, parent, year, amounts):
    model.objects.filter(**{fk_name: parent, "anio": year}).delete()
    model.objects.bulk_create(
        [
            model(**{fk_name: parent, "anio": year, "mes": month, "monto": amount})
            for month, amount in enumerate(amounts, start=1)
        ]
    )


def _monthly_rows(rows, header):
    start = _find_row(rows, header) + 1
    parsed = []
    for row in rows[start:]:
        name = str(_cell(row, 0) or "").strip()
        if not name or name.startswith(":::"):
            continue
        amounts = [money(_cell(row, month)) for month in range(1, 13)]
        parsed.append((name, amounts))
    return parsed


@transaction.atomic
def import_ventas(path):
    rows = _rows(path)
    header_index = _find_row(rows, "No. documento", column=5)
    company = EmpresaFiscal.objects.order_by("id").first() or EmpresaFiscal(razon_social="")
    for row in rows[:header_index]:
        label = str(_cell(row, 0) or "").strip().lower()
        if label.startswith("razón social") or label.startswith("razon social"):
            company.razon_social = str(_cell(row, 1) or "").strip()
            for index, cell in enumerate(row):
                text = str(cell or "").strip().lower()
                if text.startswith("desde"):
                    company.desde = as_date(_cell(row, index + 1))
                if text.startswith("hasta"):
                    company.hasta = as_date(_cell(row, index + 1))
        if label.startswith("dirección") or label.startswith("direccion"):
            company.nombre = str(_cell(row, 1) or "").strip()
    if not company.razon_social:
        raise ValueError("El libro de ventas no trae la razón social.")
    company.save()

    documents = []
    for row in rows[header_index + 1 :]:
        if _cell(row, 0) is None or _cell(row, 1) is None:
            continue
        documents.append(
            DocumentoVenta(
                registro=int(_cell(row, 0)),
                fecha=as_date(_cell(row, 1)),
                caja=str(_cell(row, 2) or "").strip(),
                tipo=str(_cell(row, 3) or "").strip(),
                serie=str(_cell(row, 4) or "").strip(),
                numero=document_number(_cell(row, 5)),
                cai=str(_cell(row, 6) or "").strip(),
                fecha_limite=as_date(_cell(row, 7)),
                rtn=text_id(_cell(row, 8)),
                cliente=str(_cell(row, 9) or "").strip(),
                condicion=str(_cell(row, 10) or "").strip(),
                forma_pago=str(_cell(row, 11) or "").strip(),
                moneda=str(_cell(row, 12) or "HNL").strip() or "HNL",
                exenta=money(_cell(row, 13)),
                exonerada=money(_cell(row, 14)),
                gravada_15=money(_cell(row, 15)),
                isv_15=money(_cell(row, 16)),
                gravada_18=money(_cell(row, 17)),
                isv_18=money(_cell(row, 18)),
                descuento=money(_cell(row, 19)),
                total=money(_cell(row, 20)),
                estado=str(_cell(row, 21) or "").strip() or "VIGENTE",
            )
        )
    DocumentoVenta.objects.all().delete()
    DocumentoVenta.objects.bulk_create(documents, batch_size=1000)
    return len(documents)


@transaction.atomic
def import_proveedores(path):
    rows = _rows(path)
    year = _year_from(rows, date.today().year)
    Proveedor.objects.all().delete()
    for name, amounts in _monthly_rows(rows, "Compras por Proveedor"):
        supplier = Proveedor.objects.create(nombre=name)
        _store_months(CompraMensual, "proveedor", supplier, year, amounts)
    return Proveedor.objects.count()


@transaction.atomic
def import_vendedores(path):
    rows = _rows(path)
    year = _year_from(rows, date.today().year)
    VendedorReporte.objects.all().delete()
    for name, amounts in _monthly_rows(rows, "Vendedores"):
        seller = VendedorReporte.objects.create(nombre=name)
        _store_months(VentaMensual, "vendedor", seller, year, amounts)
    return VendedorReporte.objects.count()


@transaction.atomic
def import_cierres(path):
    rows = _rows(path)
    start = _find_row(rows, "FECHA") + 1
    closings = []
    for row in rows[start:]:
        if _cell(row, 0) is None:
            continue
        concept = str(_cell(row, 1) or "").strip()
        match = CIERRE_RE.search(concept)
        closings.append(
            CierreDiario(
                fecha=as_date(_cell(row, 0)),
                numero=int(match.group(1)) if match else None,
                factura_desde=match.group(2) if match else "",
                factura_hasta=match.group(3) if match else "",
                concepto=concept,
                venta_libre=money(_cell(row, 2)),
                venta_gravada=money(_cell(row, 3)),
                impuesto=money(_cell(row, 4)),
                total=money(_cell(row, 5)),
            )
        )
    CierreDiario.objects.all().delete()
    CierreDiario.objects.bulk_create(closings, batch_size=500)
    return len(closings)


def import_libros(*, ventas=None, proveedores=None, vendedores=None, cierres=None):
    result = {}
    if ventas:
        result["documentos"] = import_ventas(ventas)
    if proveedores:
        result["proveedores"] = import_proveedores(proveedores)
    if vendedores:
        result["vendedores"] = import_vendedores(vendedores)
    if cierres:
        result["cierres"] = import_cierres(cierres)
    return result
