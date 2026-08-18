from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0013_configuracionsitio_platos_destacados'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracionsitio',
            name='subtitulo_inicio',
            field=models.TextField(default='Realiza tu pedido, agenda tu mesa o sigue tu entrega a domicilio sin complicaciones y en tiempo real.', help_text='Texto secundario mostrado debajo del titulo principal.'),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='titulo_inicio',
            field=models.CharField(default='Pedidos, reservas y entregas mas sencillas', help_text='Titulo principal mostrado en la portada.', max_length=160),
        ),
        migrations.CreateModel(
            name='PlatoDestacadoPortada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveSmallIntegerField(default=1, help_text='Posicion visible en la portada, del 1 al 5.', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('configuracion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='destacados_portada', to='gestion_web.configuracionsitio')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gestion_web.producto')),
            ],
            options={
                'verbose_name': 'Plato destacado de portada',
                'verbose_name_plural': 'Platos destacados de portada',
                'ordering': ('orden', 'id'),
                'constraints': [models.UniqueConstraint(fields=('configuracion', 'orden'), name='unique_orden_destacado_portada'), models.UniqueConstraint(fields=('configuracion', 'producto'), name='unique_producto_destacado_portada')],
            },
        ),
    ]