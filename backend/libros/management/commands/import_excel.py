from django.core.management.base import BaseCommand, CommandError

from libros.excel_import import import_libros


class Command(BaseCommand):
    help = "Carga en SQLite el libro de ventas, proveedores, vendedores y cierres exportados de Excel."

    def add_arguments(self, parser):
        parser.add_argument("--ventas", help="Libro de ventas (.xlsx).")
        parser.add_argument("--proveedores", help="Compras por proveedor (.xlsx).")
        parser.add_argument("--vendedores", help="Ventas por vendedor (.xlsx).")
        parser.add_argument("--cierres", help="Cierres por fecha (.xlsx).")

    def handle(self, *args, **options):
        if not any(options[key] for key in ("ventas", "proveedores", "vendedores", "cierres")):
            raise CommandError("Indica al menos un archivo con --ventas, --proveedores, --vendedores o --cierres.")
        result = import_libros(
            ventas=options["ventas"],
            proveedores=options["proveedores"],
            vendedores=options["vendedores"],
            cierres=options["cierres"],
        )
        parts = [f"{name}: {count}" for name, count in result.items()]
        self.stdout.write(self.style.SUCCESS("Importado. " + ", ".join(parts) + "."))
