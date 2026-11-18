from django.db import transaction

from .catalog import PERMISSIONS, ROLES, level_for
from .models import Permission, Role, RolePermission, User

DEMO_PASSWORD = "Pollo2026"

DEMO_USERS = [
    ("gerencia", "Gerencia", "Demo", "gerencia", True, True),
    ("contador", "Contador", "Demo", "contador", False, False),
    ("facturacion", "Facturación", "Demo", "facturacion", False, False),
    ("vendedor", "Vendedor", "Demo", "vendedor", False, False),
    ("inventario", "Inventario", "Demo", "inventario", False, False),
]


@transaction.atomic
def seed():
    roles = {}
    for item in ROLES:
        role, _created = Role.objects.update_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "summary": item["summary"],
                "description": item["description"],
                "sort_order": item["sort_order"],
                "is_system": True,
            },
        )
        roles[role.code] = role

    known_permissions = set()
    for code, module, name, description, sort_order in PERMISSIONS:
        permission, _created = Permission.objects.update_or_create(
            code=code,
            defaults={
                "module": module,
                "name": name,
                "description": description,
                "sort_order": sort_order,
            },
        )
        known_permissions.add(permission.code)
        for role in roles.values():
            RolePermission.objects.update_or_create(
                role=role,
                permission=permission,
                defaults={"level": level_for(role.code, permission.code)},
            )

    Permission.objects.exclude(code__in=known_permissions).delete()

    created_users = []
    for username, first_name, last_name, role_code, is_staff, is_superuser in DEMO_USERS:
        _user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "role": roles[role_code],
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "is_active": True,
            },
        )
        if created:
            _user.set_password(DEMO_PASSWORD)
            _user.save(update_fields=["password"])
            created_users.append(username)

    return {
        "roles": len(roles),
        "permissions": len(known_permissions),
        "users_created": created_users,
    }
