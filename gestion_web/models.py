from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator

# =====================================================================
# 1. ROLES DE USUARIO Y CLIENTE (cliente)
# =====================================================================
class Usuario(AbstractUser):
    class Roles(models.TextChoices):
        ADMINISTRADOR = 'ADMIN', 'Administrador (Dueño/Empleado)'
        EMPLEADO = 'EMPLEADO', 'Empleado'
        REPARTIDOR = 'REPARTIDOR', 'Repartidor'
        CLIENTE = 'CLIENTE', 'Cliente'

    rol = models.CharField(max_length=12, choices=Roles.choices, default=Roles.CLIENTE)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    # Evidencia de aceptación para cumplir la política de protección de datos.
    acepta_politica_datos = models.BooleanField(default=False)
    fecha_aceptacion_politica = models.DateTimeField(null=True, blank=True)
    version_politica_datos = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"


class ConfiguracionSitio(models.Model):
    nombre = models.CharField(max_length=100, default='Configuracion principal')
    fondo = models.ImageField(
        upload_to='fondos/',
        blank=True,
        null=True,
        help_text='Imagen de fondo global para todo el sistema.',
    )
    logo_principal = models.ImageField(
        upload_to='logos/',
        blank=True,
        null=True,
        help_text='Logo principal mostrado en el encabezado de la portada.',
    )
    subtitulo_logo = models.CharField(
        max_length=80,
        default='Rukullacta',
        help_text='Texto pequeño mostrado debajo del nombre principal del logo.',
    )
    mostrar_seccion_destacados = models.BooleanField(
        default=True,
        help_text='Activa o desactiva la seccion de platos destacados en la portada.',
    )
    titulo_seccion_destacados = models.CharField(
        max_length=180,
        default='Platos favoritos para empezar tu pedido',
        help_text='Titulo principal de la seccion de platos destacados.',
    )
    etiqueta_seccion_destacados = models.CharField(
        max_length=80,
        default='Seleccion destacada',
        help_text='Texto corto mostrado arriba del titulo de la seccion destacada.',
    )
    subtitulo_seccion_destacados = models.TextField(
        default='Descubre una muestra del menu con opciones listas para agregar al carrito o revisar dentro del sistema.',
        help_text='Texto secundario de la seccion de platos destacados.',
    )
    texto_boton_principal_hero = models.CharField(
        max_length=80,
        default='Explorar pedidos',
        help_text='Texto del boton principal del hero.',
    )
    enlace_boton_principal_hero = models.CharField(
        max_length=255,
        default='/menu/',
        help_text='Enlace del boton principal del hero. Puedes usar rutas relativas como /menu/.',
    )
    texto_boton_secundario_hero = models.CharField(
        max_length=80,
        default='Crear cuenta',
        help_text='Texto del boton secundario del hero.',
    )
    enlace_boton_secundario_hero = models.CharField(
        max_length=255,
        default='/registro/',
        help_text='Enlace del boton secundario del hero. Puedes usar rutas relativas como /registro/.',
    )
    delivery_min_order = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=10.00,
        help_text='Monto mínimo para aceptar pedidos a domicilio.',
    )
    delivery_standard_radius_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=8.00,
        help_text='Radio estándar de entrega alrededor de Archidona (en kilómetros).',
    )
    delivery_base_prep_minutes = models.PositiveIntegerField(
        default=20,
        help_text='Minutos base de preparación antes de despacho.',
    )
    delivery_average_speed_kmh = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=28.00,
        help_text='Velocidad promedio usada para estimar tiempo de llegada.',
    )
    delivery_out_of_range_base_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=1.50,
        help_text='Cargo fijo adicional cuando la ubicación está fuera del rango estándar.',
    )
    delivery_out_of_range_per_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.35,
        help_text='Cargo adicional por cada kilómetro fuera del rango estándar.',
    )
    delivery_tena_extra_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.75,
        help_text='Recargo extra cuando la ubicación cae en Tena o más allá.',
    )
    platos_destacados = models.ManyToManyField(
        'Producto',
        blank=True,
        related_name='configuraciones_destacadas',
        limit_choices_to={'disponible': True},
        help_text='Selecciona entre 3 y 5 platos destacados para la portada.',
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuracion del sitio'
        verbose_name_plural = 'Configuracion del sitio'

    def save(self, *args, **kwargs):
        # Mantenemos un unico registro para centralizar la configuracion visual del sitio.
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class PlatoDestacadoPortada(models.Model):
    configuracion = models.ForeignKey(
        ConfiguracionSitio,
        on_delete=models.CASCADE,
        related_name='destacados_portada',
    )
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    descripcion_corta = models.CharField(
        max_length=180,
        blank=True,
        help_text='Descripcion breve opcional mostrada debajo del nombre del plato.',
    )
    orden = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Posicion visible en la portada, del 1 al 5.',
    )

    class Meta:
        verbose_name = 'Plato destacado de portada'
        verbose_name_plural = 'Platos destacados de portada'
        ordering = ('orden', 'id')
        constraints = [
            models.UniqueConstraint(fields=['configuracion', 'orden'], name='unique_orden_destacado_portada'),
            models.UniqueConstraint(fields=['configuracion', 'producto'], name='unique_producto_destacado_portada'),
        ]

    def __str__(self):
        return f'{self.orden}. {self.producto.nombre}'


# =====================================================================
# 2. PROVEEDORES E INSUMOS (proveedor -> suministra -> insumos)
# =====================================================================
class Proveedor(models.Model):
    nombre_empresa = models.CharField(max_length=100)
    contacto_nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    correo_electronico = models.EmailField()

    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre_empresa


class Insumo(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='insumos', null=True, blank=True)
    nombre = models.CharField(max_length=100, unique=True)
    stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unidad_medida = models.CharField(max_length=20)  # Kg, Litros, Unidades

    class Meta:
        verbose_name = 'Insumo'
        verbose_name_plural = "Insumos y Bodega"

    def __str__(self):
        return f"{self.nombre} ({self.stock} {self.unidad_medida})"


# =====================================================================
# 3. PLATOS / PRODUCTOS (platos -> requiere -> insumos)
# =====================================================================
class Producto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)])
    disponible = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    insumos = models.ManyToManyField(Insumo, through='Insumo_Producto', related_name='productos')

    class Meta:
        verbose_name = 'Plato'
        verbose_name_plural = 'Platos'

    def __str__(self):
        return self.nombre


class Insumo_Producto(models.Model):
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_utilizada = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Insumo por Plato'
        verbose_name_plural = "Insumos por Plato"

    def __str__(self):
        return f"{self.cantidad_utilizada} de {self.insumo.nombre} para {self.producto.nombre}"


# =====================================================================
# 4. MESA Y RESERVA (cliente -> solicita -> reserva -> asigna -> mesa)
# =====================================================================
class Mesa(models.Model):
    # Enumeración de estados operativos de mesa.
    # Esta lista define exactamente qué estados puede elegir el personal
    # desde el panel admin para controlar la disponibilidad al cliente.
    class EstadoMesa(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        OCUPADA = 'OCUPADA', 'Ocupada'
        MANTENIMIENTO = 'MANTENIMIENTO', 'Mantenimiento'

    # Número único visible para cliente y personal (ej: Mesa 1, Mesa 2, etc.).
    numero = models.IntegerField(unique=True)
    # Capacidad máxima de personas que puede atender la mesa.
    capacidad = models.IntegerField()
    # Campo legado de compatibilidad.
    # Se mantiene para no romper datos/código anterior mientras se migra
    # todo el sistema al nuevo campo de estado.
    disponible = models.BooleanField(default=True)
    # Nuevo campo de negocio para gestionar estados desde admin/empleado.
    # Es la fuente de verdad que usa la lógica de reservas para filtrar mesas.
    estado = models.CharField(
        max_length=20,
        choices=EstadoMesa.choices,
        default=EstadoMesa.DISPONIBLE,
    )

    # Sincroniza automáticamente el campo legado `disponible`
    # con el nuevo estado para evitar inconsistencias durante la transición.
    def save(self, *args, **kwargs):
        self.disponible = self.estado == self.EstadoMesa.DISPONIBLE
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Mesa #{self.numero} (Cap. {self.capacidad} pers.)"

    class Meta:
        verbose_name = 'Mesa'
        verbose_name_plural = 'Mesas'


class Reserva(models.Model):
    class EstadoReserva(models.TextChoices):
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        FINALIZADA = 'FINALIZADA', 'Asistida'
        CANCELADA = 'CANCELADA', 'Cancelada'

    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='mis_reservas')
    mesa = models.ForeignKey(Mesa, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')
    # Vinculamos la reserva con un pedido opcional para guardar el pre-pedido de platos sin romper reservas simples.
    pedido = models.ForeignKey('Pedido', on_delete=models.SET_NULL, null=True, blank=True, related_name='reserva')
    fecha = models.DateField()
    hora = models.TimeField()
    numero_personas = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    estado = models.CharField(max_length=15, choices=EstadoReserva.choices, default=EstadoReserva.CONFIRMADA)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f"Reserva de {self.cliente.username} - {self.fecha}"


# =====================================================================
# 5. PEDIDOS Y DETALLE (cliente -> realiza -> pedidos -> contiene -> detalle)
# =====================================================================
class Pedido(models.Model):
    class TipoPedido(models.TextChoices):
        LOCAL = 'LOCAL', 'Consumo en Local'
        DOMICILIO = 'DOMICILIO', 'Entrega a Domicilio'

    class EstadoPedido(models.TextChoices):
        PENDIENTE_PAGO = 'PENDIENTE_PAGO', 'Pendiente de pago'
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PAGADO = 'PAGADO', 'Pagado'
        PREPARANDO = 'PREPARANDO', 'En Cocina'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='mis_pedidos')
    tipo = models.CharField(max_length=15, choices=TipoPedido.choices, default=TipoPedido.LOCAL)
    estado = models.CharField(max_length=15, choices=EstadoPedido.choices, default=EstadoPedido.PENDIENTE)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.username} ({self.estado})"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedido'

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"


# =====================================================================
# 6. ENTREGA (pedidos -> genera -> entrega)
# =====================================================================
class Entrega(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='entrega')
    direccion = models.TextField()
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    distancia_km = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    tiempo_estimado_minutos = models.PositiveIntegerField(default=30)
    fuera_rango_estandar = models.BooleanField(default=False)
    cargo_adicional = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    estado_envio = models.CharField(max_length=20, default='En camino')

    class Meta:
        verbose_name = 'Entrega'
        verbose_name_plural = 'Entregas'

    def __str__(self):
        return f"Entrega Pedido #{self.pedido.id}"


# =====================================================================
# 7. PAGOS Y FACTURA (pedidos -> realiza -> pagos -> genera -> factura)
# =====================================================================
class Pago(models.Model):
    class EstadoPago(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        REPORTADO_REPARTIDOR = 'REPORTADO_REPARTIDOR', 'Reportado por repartidor'
        CONFIRMADO = 'CONFIRMADO', 'Confirmado'

    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='pago')
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    metodo_pago = models.CharField(max_length=50) # Efectivo, Transferencia, Tarjeta
    estado = models.CharField(max_length=24, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE)
    confirmado_por = models.ForeignKey(
        Usuario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='pagos_confirmados',
    )
    confirmado_en = models.DateTimeField(null=True, blank=True)
    fecha_pago = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago #{self.id} de Pedido #{self.pedido.id}"


class Factura(models.Model):
    pago = models.OneToOneField(Pago, on_delete=models.CASCADE, related_name='factura')
    numero_factura = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'

    def __str__(self):
        return f"Factura {self.numero_factura}"