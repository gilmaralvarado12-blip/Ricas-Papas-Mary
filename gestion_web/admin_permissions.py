class RolAdminMixin:
    """Limita cada modelo del Admin según el rol operativo del usuario."""

    roles_permitidos = ('ADMIN',)
    roles_para_agregar = ()
    roles_para_cambiar = ()
    roles_para_eliminar = ()

    def _es_administrador(self, request):
        return getattr(request.user, 'rol', None) == 'ADMIN'

    def _rol_permitido(self, request, roles):
        return getattr(request.user, 'rol', None) in roles

    def has_module_permission(self, request):
        return self._es_administrador(request) or self._rol_permitido(request, self.roles_permitidos)

    def has_view_permission(self, request, obj=None):
        return self._es_administrador(request) or self._rol_permitido(request, self.roles_permitidos)

    def has_add_permission(self, request):
        return self._es_administrador(request) or self._rol_permitido(request, self.roles_para_agregar)

    def has_change_permission(self, request, obj=None):
        return self._es_administrador(request) or self._rol_permitido(request, self.roles_para_cambiar)

    def has_delete_permission(self, request, obj=None):
        return self._es_administrador(request) or self._rol_permitido(request, self.roles_para_eliminar)


class OperacionEmpleadoMixin(RolAdminMixin):
    roles_permitidos = ('ADMIN', 'EMPLEADO')
    roles_para_cambiar = ('ADMIN', 'EMPLEADO')


class EntregaPersonalMixin(RolAdminMixin):
    roles_permitidos = ('ADMIN', 'EMPLEADO', 'REPARTIDOR')
    roles_para_cambiar = ('ADMIN', 'EMPLEADO', 'REPARTIDOR')
