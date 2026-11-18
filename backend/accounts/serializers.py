import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .catalog import MODULE_LABELS
from .models import Role, RoleCode, User

USERNAME_PATTERN = re.compile(r"[a-z0-9._-]{3,150}")


def grant_payload(grant):
    permission = grant.permission
    return {
        "code": permission.code,
        "module": permission.module,
        "module_label": MODULE_LABELS.get(permission.module, permission.module),
        "name": permission.name,
        "description": permission.description,
        "level": grant.level,
        "level_label": grant.get_level_display(),
        "sort_order": permission.sort_order,
    }


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    active_users = serializers.IntegerField(read_only=True)

    class Meta:
        model = Role
        fields = (
            "id",
            "code",
            "name",
            "summary",
            "description",
            "sort_order",
            "active_users",
            "permissions",
        )

    def get_permissions(self, role):
        grants = sorted(role.grants.all(), key=lambda grant: grant.permission.sort_order)
        return [grant_payload(grant) for grant in grants]


class RoleBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "code", "name", "summary")


class UserSerializer(serializers.ModelSerializer):
    role = RoleBriefSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "is_active",
            "role",
            "permissions",
            "last_login",
            "date_joined",
        )

    def get_full_name(self, user):
        full_name = user.get_full_name().strip()
        return full_name or user.username

    def get_permissions(self, user):
        if not user.role_id:
            return []
        grants = sorted(user.role.grants.all(), key=lambda grant: grant.permission.sort_order)
        return [grant_payload(grant) for grant in grants]


class UserWriteSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(
        source="role",
        queryset=Role.objects.order_by("sort_order"),
        error_messages={
            "required": "Elige un rol.",
            "does_not_exist": "Ese rol no existe.",
            "incorrect_type": "El rol no es válido.",
        },
    )
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone",
            "is_active",
            "role_id",
        )
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
            "email": {"required": False, "allow_blank": True},
            "phone": {"required": False, "allow_blank": True},
            "is_active": {"required": False},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields.pop("username")

    def validate_username(self, value):
        value = value.strip().lower()
        if not USERNAME_PATTERN.fullmatch(value):
            raise serializers.ValidationError(
                "Usa de 3 a 150 caracteres: letras minúsculas, números, punto, guion o guion bajo."
            )
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ese usuario ya existe.")
        return value

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El nombre es obligatorio.")
        return value

    def validate_last_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El apellido es obligatorio.")
        return value

    def validate_email(self, value):
        return value.strip()

    def validate_phone(self, value):
        return value.strip()

    def validate(self, attrs):
        password = attrs.get("password")
        if self.instance is None and not password:
            raise serializers.ValidationError({"password": "La contraseña es obligatoria."})
        if password:
            tentative = self.instance or User(
                username=attrs.get("username", ""),
                first_name=attrs.get("first_name", ""),
                last_name=attrs.get("last_name", ""),
                email=attrs.get("email", ""),
            )
            try:
                validate_password(password, tentative)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"password": list(exc.messages)}) from exc

        if self.instance is not None:
            next_role = attrs.get("role", self.instance.role)
            next_active = attrs.get("is_active", self.instance.is_active)
            was_active_gerencia = (
                self.instance.is_active
                and self.instance.role_id
                and self.instance.role.code == RoleCode.GERENCIA
            )
            stays_gerencia = (
                next_active and next_role is not None and next_role.code == RoleCode.GERENCIA
            )
            if was_active_gerencia and not stays_gerencia:
                still_there = (
                    User.objects.filter(is_active=True, role__code=RoleCode.GERENCIA)
                    .exclude(pk=self.instance.pk)
                    .exists()
                )
                if not still_there:
                    raise serializers.ValidationError(
                        "Debe quedar al menos un usuario activo con el rol de admin."
                    )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.setdefault("is_active", True)
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        instance._access_map = None
        return instance
