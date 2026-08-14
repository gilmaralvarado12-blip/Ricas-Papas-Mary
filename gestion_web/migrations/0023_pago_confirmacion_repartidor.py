from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0022_configuracionsitio_delivery_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='pago',
            name='estado',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente'),
                    ('REPORTADO_REPARTIDOR', 'Reportado por repartidor'),
                    ('CONFIRMADO', 'Confirmado'),
                ],
                default='PENDIENTE',
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name='pago',
            name='confirmado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pagos_confirmados',
                to='gestion_web.usuario',
            ),
        ),
        migrations.AddField(
            model_name='pago',
            name='confirmado_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
