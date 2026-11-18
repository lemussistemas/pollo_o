from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import require_access

from .models import CierreDiario, DocumentoVenta, EmpresaFiscal, Proveedor, VendedorReporte
from .serializers import CierreDiarioSerializer, DocumentoVentaSerializer

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


class DocumentoPagination(PageNumberPagination):
    page_size = 25


def _money(value):
    return f"{(value or 0):.2f}"


def _months(items):
    amounts = ["0.00"] * 12
    for item in items:
        amounts[item.mes - 1] = _money(item.monto)
    return amounts


class LibroResumenView(APIView):
    permission_classes = [IsAuthenticated, require_access("contabilidad.libros")]

    def get(self, request):
        company = EmpresaFiscal.objects.order_by("id").first()
        documents = DocumentoVenta.objects.all()
        zero = Decimal("0.00")
        totals = documents.aggregate(
            total=Coalesce(Sum("total"), zero),
            exenta=Coalesce(Sum("exenta"), zero),
            exonerada=Coalesce(Sum("exonerada"), zero),
            gravada_15=Coalesce(Sum("gravada_15"), zero),
            isv_15=Coalesce(Sum("isv_15"), zero),
            gravada_18=Coalesce(Sum("gravada_18"), zero),
            isv_18=Coalesce(Sum("isv_18"), zero),
            descuento=Coalesce(Sum("descuento"), zero),
        )
        by_state = {row["estado"]: row["n"] for row in documents.values("estado").annotate(n=Count("id"))}
        by_condition = {
            row["condicion"]: {"documentos": row["n"], "total": _money(row["total"])}
            for row in documents.values("condicion").annotate(n=Count("id"), total=Sum("total"))
        }
        return Response(
            {
                "razon_social": company.razon_social if company else "",
                "nombre": company.nombre if company else "",
                "desde": company.desde if company else None,
                "hasta": company.hasta if company else None,
                "documentos": documents.count(),
                "vigentes": by_state.get("VIGENTE", 0),
                "anulados": by_state.get("ANULADO", 0),
                "clientes": documents.values("cliente").distinct().count(),
                "cajas": list(documents.order_by("caja").values_list("caja", flat=True).distinct()),
                "ventas_netas": _money(totals["total"]),
                "exentas": _money(totals["exenta"]),
                "exoneradas": _money(totals["exonerada"]),
                "gravada_15": _money(totals["gravada_15"]),
                "isv_15": _money(totals["isv_15"]),
                "gravada_18": _money(totals["gravada_18"]),
                "isv_18": _money(totals["isv_18"]),
                "descuentos": _money(totals["descuento"]),
                "contado": by_condition.get("CONTADO", {"documentos": 0, "total": "0.00"}),
                "credito": by_condition.get("CREDITO", {"documentos": 0, "total": "0.00"}),
            }
        )


class DocumentoListView(APIView):
    permission_classes = [IsAuthenticated, require_access("contabilidad.libros")]

    def get(self, request):
        queryset = DocumentoVenta.objects.all()
        params = request.query_params
        query = params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(cliente__icontains=query)
                | Q(numero__icontains=query)
                | Q(rtn__icontains=query)
                | Q(serie__icontains=query)
            )
        if params.get("caja"):
            queryset = queryset.filter(caja=params["caja"])
        if params.get("condicion"):
            queryset = queryset.filter(condicion=params["condicion"])
        if params.get("estado"):
            queryset = queryset.filter(estado=params["estado"])
        if params.get("desde"):
            queryset = queryset.filter(fecha__gte=params["desde"])
        if params.get("hasta"):
            queryset = queryset.filter(fecha__lte=params["hasta"])
        page = DocumentoPagination()
        chunk = page.paginate_queryset(queryset, request, view=self)
        return page.get_paginated_response(DocumentoVentaSerializer(chunk, many=True).data)


class ProveedorListView(APIView):
    permission_classes = [IsAuthenticated, require_access("contabilidad.libros")]

    def get(self, request):
        payload = []
        for supplier in Proveedor.objects.prefetch_related("compras"):
            months = _months(supplier.compras.all())
            payload.append(
                {
                    "id": supplier.id,
                    "nombre": supplier.nombre,
                    "meses": months,
                    "total": _money(sum(compra.monto for compra in supplier.compras.all())),
                }
            )
        payload.sort(key=lambda item: Decimal(item["total"]), reverse=True)
        return Response({"meses": MESES, "proveedores": payload})


class VendedorReporteListView(APIView):
    permission_classes = [IsAuthenticated, require_access("contabilidad.libros")]

    def get(self, request):
        payload = []
        for seller in VendedorReporte.objects.prefetch_related("ventas"):
            payload.append(
                {
                    "id": seller.id,
                    "nombre": seller.nombre,
                    "meses": _months(seller.ventas.all()),
                    "total": _money(sum(sale.monto for sale in seller.ventas.all())),
                }
            )
        payload.sort(key=lambda item: Decimal(item["total"]), reverse=True)
        return Response({"meses": MESES, "vendedores": payload})


class CierreListView(APIView):
    permission_classes = [IsAuthenticated, require_access("contabilidad.libros")]

    def get(self, request):
        closings = CierreDiario.objects.all()
        total = closings.aggregate(total=Coalesce(Sum("total"), Decimal("0.00")))["total"]
        return Response(
            {
                "total": _money(total),
                "cierres": CierreDiarioSerializer(closings, many=True).data,
            }
        )
