from django.core.management.base import BaseCommand

from accounts.seed import DEMO_PASSWORD, seed


class Command(BaseCommand):
    help = "Crea los cinco roles, sus permisos y los usuarios de demostración."

    def handle(self, *args, **options):
        result = seed()
        self.stdout.write(
            self.style.SUCCESS(
                f"Roles: {result['roles']}. Permisos: {result['permissions']}."
            )
        )
        if result["users_created"]:
            names = ", ".join(result["users_created"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Usuarios nuevos: {names}. Contraseña de demostración: {DEMO_PASSWORD}"
                )
            )
        else:
            self.stdout.write(
                "Los usuarios de demostración ya existían. No se cambió su contraseña."
            )
