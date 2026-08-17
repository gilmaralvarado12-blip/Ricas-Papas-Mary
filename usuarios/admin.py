from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from gestion_web.models import Usuario
from .models import DueñoProxy, EmpleadoProxy, RepartidorProxy


class UsuarioRolAdminMixin:
    rol_value = None

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if self.rol_value is None:
            return qs
        return qs.filter(rol=self.rol_value)

    def save_model(self, request, obj, form, change):
        if self.rol_value is not None:
            obj.rol = self.rol_value
        super().save_model(request, obj, form, change)


class DueñoAdmin(UsuarioRolAdminMixin, UserAdmin):
    list_display = ('username', 'email', 'telefono', 'rol', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'telefono')
    ordering = ('username',)
    fieldsets = UserAdmin.fieldsets + (
        ('Información del sistema', {'fields': ('rol', 'telefono', 'acepta_politica_datos', 'fecha_aceptacion_politica', 'version_politica_datos')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información del sistema', {'fields': ('rol', 'telefono', 'is_active')}),
    )
    rol_value = Usuario.Roles.ADMINISTRADOR


class EmpleadoAdmin(UsuarioRolAdminMixin, UserAdmin):
    list_display = ('username', 'email', 'telefono', 'rol', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'telefono')
    ordering = ('username',)
    fieldsets = UserAdmin.fieldsets + (
        ('Información del sistema', {'fields': ('rol', 'telefono', 'acepta_politica_datos', 'fecha_aceptacion_politica', 'version_politica_datos')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información del sistema', {'fields': ('rol', 'telefono', 'is_active')}),
    )
    rol_value = Usuario.Roles.EMPLEADO


class RepartidorAdmin(UsuarioRolAdminMixin, UserAdmin):
    list_display = ('username', 'email', 'telefono', 'rol', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'telefono')
    ordering = ('username',)
    fieldsets = UserAdmin.fieldsets + (
        ('Información del sistema', {'fields': ('rol', 'telefono', 'acepta_politica_datos', 'fecha_aceptacion_politica', 'version_politica_datos')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información del sistema', {'fields': ('rol', 'telefono', 'is_active')}),
    )
    rol_value = Usuario.Roles.REPARTIDOR


@admin.register(DueñoProxy)
class DueñoProxyAdmin(DueñoAdmin):
    pass


@admin.register(EmpleadoProxy)
class EmpleadoProxyAdmin(EmpleadoAdmin):
    pass


@admin.register(RepartidorProxy)
class RepartidorProxyAdmin(RepartidorAdmin):
    pass
