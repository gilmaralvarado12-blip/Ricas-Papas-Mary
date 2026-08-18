from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.utils.html import format_html
from .models import (
    ConfiguracionSitio, PlatoDestacadoPortada, Usuario, Proveedor, Insumo, Producto, Insumo_Producto,
    Mesa, Reserva, Pedido, DetallePedido, Entrega
)
from .admin_permissions import EntregaPersonalMixin, OperacionEmpleadoMixin, RolAdminMixin


class ConfiguracionSitioAdminForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionSitio
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        field_help_texts = {
            'nombre': 'Nombre interno de esta configuracion general del sitio.',
            'fondo': 'Imagen de fondo global aplicada en todas las paginas del sistema.',
            'logo_principal': 'Logo que se muestra en el encabezado de la portada.',
            'subtitulo_logo': 'Texto pequeño que aparece debajo del nombre principal del logo.',
            'texto_boton_principal_hero': 'Texto visible del boton principal de la portada.',
            'enlace_boton_principal_hero': 'Destino del boton principal de la portada.',
            'texto_boton_secundario_hero': 'Texto visible del boton secundario de la portada.',
            'enlace_boton_secundario_hero': 'Destino del boton secundario de la portada.',
            'mostrar_seccion_destacados': 'Activa o desactiva la seccion de platos recomendados en la portada.',
            'etiqueta_seccion_destacados': 'Etiqueta corta sobre el titulo de platos recomendados.',
            'titulo_seccion_destacados': 'Titulo principal de la seccion de platos recomendados.',
            'subtitulo_seccion_destacados': 'Texto secundario de la seccion de platos recomendados.',
            'platos_destacados': 'Seleccion de respaldo cuando no se configuran platos recomendados ordenados.',
            'delivery_min_order': 'Monto mínimo requerido para aceptar pedidos a domicilio.',
            'delivery_standard_radius_km': 'Radio estándar de cobertura en kilómetros (centro Archidona).',
            'delivery_base_prep_minutes': 'Minutos base de preparación antes de iniciar la entrega.',
            'delivery_average_speed_kmh': 'Velocidad promedio para cálculo de ETA.',
            'delivery_out_of_range_base_fee': 'Cargo fijo cuando el cliente está fuera del rango estándar.',
            'delivery_out_of_range_per_km': 'Cargo por cada km adicional fuera del rango estándar.',
            'delivery_tena_extra_fee': 'Recargo adicional cuando la ubicación está en Tena o más allá.',
        }

        for field_name, text in field_help_texts.items():
            if field_name in self.fields:
                self.fields[field_name].help_text = text

    def _normalize_link_value(self, value, fallback):
        cleaned = (value or '').strip()
        if not cleaned:
            return fallback

        # Permitimos enlaces absolutos o rutas relativas; normalizamos texto plano a ruta.
        if cleaned.startswith('http://') or cleaned.startswith('https://') or cleaned.startswith('/'):
            return cleaned
        return '/' + cleaned

    def clean_enlace_boton_principal_hero(self):
        value = self.cleaned_data.get('enlace_boton_principal_hero')
        return self._normalize_link_value(value, '/menu/')

    def clean_enlace_boton_secundario_hero(self):
        value = self.cleaned_data.get('enlace_boton_secundario_hero')
        return self._normalize_link_value(value, '/registro/')

    def clean_platos_destacados(self):
        platos_destacados = self.cleaned_data.get('platos_destacados')
        if platos_destacados and platos_destacados.count() > 5:
            raise forms.ValidationError('Solo puedes seleccionar hasta 5 platos destacados.')
        return platos_destacados


class PlatoDestacadoPortadaInline(admin.TabularInline):
    model = PlatoDestacadoPortada
    verbose_name = 'Plato recomendado'
    verbose_name_plural = 'Platos recomendados'
    extra = 1
    max_num = 5
    min_num = 0
    autocomplete_fields = ('producto',)
    readonly_fields = ('drag_handle', 'producto_preview')
    fields = ('drag_handle', 'orden', 'producto', 'producto_preview', 'descripcion_corta')

    def drag_handle(self, obj):
        return format_html('<span class="rpm-drag-handle" title="Arrastrar para ordenar">↕</span>')

    drag_handle.short_description = 'Ordenar'

    def producto_preview(self, obj):
        if not obj or not obj.producto:
            return 'Selecciona un plato.'
        if obj.producto.imagen:
            return format_html(
                '<div style="display:flex; align-items:center; gap:8px;">'
                '<img src="{}" alt="{}" style="width:44px; height:44px; object-fit:cover; border-radius:8px; border:1px solid #e5e7eb;"/>'
                '<strong>{}</strong>'
                '</div>',
                obj.producto.imagen.url,
                obj.producto.nombre,
                obj.producto.nombre,
            )
        return format_html('<strong>{}</strong> <span style="color:#6b7280;">(sin imagen)</span>', obj.producto.nombre)

    producto_preview.short_description = 'Vista previa'


@admin.register(ConfiguracionSitio)
class ConfiguracionSitioAdmin(RolAdminMixin, admin.ModelAdmin):
    form = ConfiguracionSitioAdminForm
    list_display = ('nombre', 'mostrar_seccion_destacados', 'actualizado_en')
    filter_horizontal = ('platos_destacados',)
    inlines = [PlatoDestacadoPortadaInline]
    readonly_fields = ('logo_principal_preview', 'fondo_preview', 'actualizado_en')
    search_fields = ('nombre', 'titulo_seccion_destacados')
    fieldsets = (
        ('Identidad visual', {
            'description': 'Elementos base de marca visibles en la parte superior de la portada.',
            'fields': (
                'nombre',
                'logo_principal',
                'logo_principal_preview',
                'subtitulo_logo',
                'actualizado_en',
            )
        }),
        ('Seccion principal de portada', {
            'description': 'Fondo global aplicado a todas las paginas del sistema.',
            'fields': (
                'fondo',
                'fondo_preview',
            )
        }),
        ('Botones de la portada', {
            'classes': ('collapse',),
            'description': 'Configura textos y enlaces de accion principales de la portada.',
            'fields': (
                'texto_boton_principal_hero',
                'enlace_boton_principal_hero',
                'texto_boton_secundario_hero',
                'enlace_boton_secundario_hero',
            )
        }),
        ('Texto y visibilidad de platos recomendados', {
            'description': 'Controla visibilidad y textos de la grilla de platos recomendados en la portada.',
            'fields': (
                'mostrar_seccion_destacados',
                'etiqueta_seccion_destacados',
                'titulo_seccion_destacados',
                'subtitulo_seccion_destacados',
            )
        }),
        ('Reglas de entrega a domicilio', {
            'description': 'Parámetros operativos para ETA, rango y cargos adicionales de pedidos a domicilio.',
            'fields': (
                'delivery_min_order',
                'delivery_standard_radius_km',
                'delivery_base_prep_minutes',
                'delivery_average_speed_kmh',
                'delivery_out_of_range_base_fee',
                'delivery_out_of_range_per_km',
                'delivery_tena_extra_fee',
            )
        }),
        ('Opciones de respaldo', {
            'classes': ('collapse',),
            'description': 'Si no configuras platos recomendados ordenados abajo, se usa esta seleccion como respaldo.',
            'fields': ('platos_destacados',)
        }),
    )

    def logo_principal_preview(self, obj):
        if not obj or not obj.logo_principal:
            return 'No hay logo cargado.'
        return format_html(
            '<img src="{}" alt="Logo actual" style="max-height: 72px; border-radius: 10px; border: 1px solid #e5e7eb; padding: 4px; background: #fff;"/>',
            obj.logo_principal.url,
        )

    logo_principal_preview.short_description = 'Vista previa del logo'

    def fondo_preview(self, obj):
        if not obj or not obj.fondo:
            return 'No hay fondo cargado.'
        return format_html(
            '<img src="{}" alt="Fondo actual" style="max-width: 320px; border-radius: 10px; border: 1px solid #e5e7eb;"/>',
            obj.fondo.url,
        )

    fondo_preview.short_description = 'Vista previa del fondo'

    def has_add_permission(self, request):
        return not ConfiguracionSitio.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    class Media:
        js = ('gestion_web/js/admin_destacados_sortable.js',)

# Configuración en el Admin para Django
@admin.register(Usuario)
class UsuarioAdmin(RolAdminMixin, UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            'Información del sistema',
            {
                'fields': (
                    'rol',
                    'telefono',
                    'acepta_politica_datos',
                    'fecha_aceptacion_politica',
                    'version_politica_datos',
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'Información del sistema',
            {
                'fields': (
                    'rol',
                    'telefono',
                    'is_active',
                )
            },
        ),
    )
    list_display = (
        'username',
        'email',
        'rol',
        'telefono',
        'acepta_politica_datos',
        'fecha_aceptacion_politica',
        'is_staff',
    )
    list_filter = ('rol', 'is_staff', 'is_active', 'acepta_politica_datos')

@admin.register(Proveedor)
class ProveedorAdmin(RolAdminMixin, admin.ModelAdmin):
    list_display = ('nombre_empresa', 'contacto_nombre', 'telefono', 'correo_electronico')

@admin.register(Insumo)
class InsumoAdmin(RolAdminMixin, admin.ModelAdmin):
    list_display = ('nombre', 'stock', 'unidad_medida', 'proveedor')
    list_filter = ('proveedor',)

class InsumoProductoInline(admin.TabularInline):
    model = Insumo_Producto
    extra = 1

@admin.register(Producto)
class ProductoAdmin(RolAdminMixin, admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'disponible')
    list_filter = ('disponible',)
    search_fields = ('nombre', 'descripcion')
    inlines = [InsumoProductoInline]
    actions = ['delete_duplicate_productos']

    def delete_duplicate_productos(self, request, queryset):
        from django.contrib import messages
        seen = {}
        to_delete = []
        for p in Producto.objects.all().order_by('id'):
            key = p.nombre.strip().lower()
            if key in seen:
                to_delete.append(p.id)
            else:
                seen[key] = p.id
        if to_delete:
            deleted_count, _ = Producto.objects.filter(id__in=to_delete).delete()
            messages.info(request, f'Se eliminaron {deleted_count} platos duplicados.')
        else:
            messages.info(request, 'No se encontraron platos duplicados.')
    delete_duplicate_productos.short_description = 'Eliminar platos duplicados (por nombre)'

@admin.register(Mesa)
class MesaAdmin(OperacionEmpleadoMixin, admin.ModelAdmin):
    # Mostramos el estado para que el equipo operativo vea rápido qué mesas
    # están listas para reserva, cuáles están ocupadas y cuáles en mantenimiento.
    list_display = ('numero', 'capacidad', 'estado', 'disponible')
    # Habilita edición rápida directa desde la grilla (sin abrir detalle).
    # Esto conecta el panel del empleado/admin con la experiencia del cliente:
    # cuando aquí cambian estado, la vista del cliente filtra automáticamente.
    list_editable = ['estado']
    # Filtro útil para administración diaria por estado operativo.
    list_filter = ('estado',)

@admin.register(Reserva)
class ReservaAdmin(OperacionEmpleadoMixin, admin.ModelAdmin):
    list_display = ('cliente', 'mesa', 'pedido_estado', 'fecha', 'hora', 'numero_personas', 'estado')
    list_filter = ('estado', 'fecha')
    list_select_related = ('cliente', 'mesa', 'pedido')
    readonly_fields = ('platos_seleccionados',)
    fieldsets = (
        (None, {
            'fields': (
                'cliente',
                'mesa',
                'pedido',
                'platos_seleccionados',
                'fecha',
                'hora',
                'numero_personas',
                'estado',
                'notes',
            )
        }),
    )
    actions = ['delete_duplicate_reservas']

    # Mostramos el estado del pedido asociado para identificar rápido si la reserva incluye pre-pedido de platos.
    def pedido_estado(self, obj):
        if not obj.pedido:
            return 'No incluye platos'
        return obj.pedido.get_estado_display()

    pedido_estado.short_description = 'Consumo'

    # Mostramos los platos elegidos por el cliente dentro del pedido vinculado a la reserva.
    def platos_seleccionados(self, obj):
        if not obj.pedido:
            return 'No incluye platos'

        detalles = obj.pedido.detalles.select_related('producto').all()
        if not detalles:
            return 'No incluye platos'

        return ', '.join(f'{detalle.cantidad}x {detalle.producto.nombre}' for detalle in detalles)

    platos_seleccionados.short_description = 'Platos elegidos'

    def delete_duplicate_reservas(self, request, queryset):
        # elimina duplicados basados en cliente, mesa, fecha, hora y numero_personas
        from django.contrib import messages
        seen = set()
        to_delete = []
        qs = Reserva.objects.all().order_by('cliente_id','fecha','hora')
        for r in qs:
            key = (r.cliente_id, r.mesa_id if r.mesa_id else 0, str(r.fecha), str(r.hora), r.numero_personas)
            if key in seen:
                to_delete.append(r.id)
            else:
                seen.add(key)
        if to_delete:
            deleted_count, _ = Reserva.objects.filter(id__in=to_delete).delete()
            messages.info(request, f'Se eliminaron {deleted_count} reservas duplicadas.')
        else:
            messages.info(request, 'No se encontraron reservas duplicadas.')
    delete_duplicate_reservas.short_description = 'Eliminar reservas duplicadas'

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1

@admin.register(Pedido)
class PedidoAdmin(OperacionEmpleadoMixin, admin.ModelAdmin):
    list_display = ('id', 'cliente', 'tipo', 'estado', 'total', 'fecha_creacion')
    list_filter = ('tipo', 'estado', 'fecha_creacion')
    inlines = [DetallePedidoInline]
    actions = ['delete_duplicate_pedidos']

    def delete_duplicate_pedidos(self, request, queryset):
        from django.contrib import messages
        seen = set()
        to_delete = []
        qs = Pedido.objects.all().order_by('cliente_id','fecha_creacion')
        for p in qs:
            key = (p.cliente_id, p.fecha_creacion.date(), float(p.total), p.estado)
            if key in seen:
                to_delete.append(p.id)
            else:
                seen.add(key)
        if to_delete:
            deleted_count, _ = Pedido.objects.filter(id__in=to_delete).delete()
            messages.info(request, f'Se eliminaron {deleted_count} pedidos duplicados.')
        else:
            messages.info(request, 'No se encontraron pedidos duplicados.')
    delete_duplicate_pedidos.short_description = 'Eliminar pedidos duplicados'

@admin.register(Entrega)
class EntregaAdmin(EntregaPersonalMixin, admin.ModelAdmin):
    list_display = (
        'pedido',
        'direccion',
        'latitud',
        'longitud',
        'distancia_km',
        'tiempo_estimado_minutos',
        'fuera_rango_estandar',
        'cargo_adicional',
        'estado_envio',
        'estado_pago',
        'mapa_google',
    )
    list_filter = ('estado_envio',)
    search_fields = ('pedido__id', 'pedido__cliente__username', 'direccion')
    list_select_related = ('pedido',)
    fieldsets = (
        (None, {
            'fields': (
                'pedido',
                'direccion',
                'latitud',
                'longitud',
                'distancia_km',
                'tiempo_estimado_minutos',
                'fuera_rango_estandar',
                'cargo_adicional',
                'estado_envio',
                'estado_pago',
                'mapa_google',
            )
        }),
    )
    readonly_fields = ('pedido', 'estado_pago', 'mapa_google')

    def estado_pago(self, obj):
        pago = getattr(obj.pedido, 'pago', None)
        if not pago:
            return 'Sin registro'
        return pago.get_estado_display()

    estado_pago.short_description = 'Estado del pago'

    def mapa_google(self, obj):
        if not obj:
            return 'Sin ubicación'

        if obj.latitud is not None and obj.longitud is not None:
            destination = f'{obj.latitud},{obj.longitud}'
        elif obj.direccion:
            from urllib.parse import quote_plus
            destination = quote_plus(obj.direccion)
        else:
            return 'Sin ubicación'

        map_url = f'https://www.google.com/maps?q={destination}'
        route_url = f'https://www.google.com/maps/dir/?api=1&destination={destination}'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Ver mapa</a> | '
            '<a href="{}" target="_blank" rel="noopener">Cómo llegar</a>',
            map_url,
            route_url,
        )

    mapa_google.short_description = 'Ubicación en mapa'
