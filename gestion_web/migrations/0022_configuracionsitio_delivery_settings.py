from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0021_entrega_logica_distancia_eta'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracionsitio',
            name='delivery_average_speed_kmh',
            field=models.DecimalField(decimal_places=2, default=28.0, help_text='Velocidad promedio usada para estimar tiempo de llegada.', max_digits=5),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='delivery_base_prep_minutes',
            field=models.PositiveIntegerField(default=20, help_text='Minutos base de preparación antes de despacho.'),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='delivery_min_order',
            field=models.DecimalField(decimal_places=2, default=10.0, help_text='Monto mínimo para aceptar pedidos a domicilio.', max_digits=8),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='delivery_out_of_range_base_fee',
            field=models.DecimalField(decimal_places=2, default=1.5, help_text='Cargo fijo adicional cuando la ubicación está fuera del rango estándar.', max_digits=8),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='delivery_out_of_range_per_km',
            field=models.DecimalField(decimal_places=2, default=0.35, help_text='Cargo adicional por cada kilómetro fuera del rango estándar.', max_digits=8),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='delivery_standard_radius_km',
            field=models.DecimalField(decimal_places=2, default=8.0, help_text='Radio estándar de entrega alrededor de Archidona (en kilómetros).', max_digits=6),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='delivery_tena_extra_fee',
            field=models.DecimalField(decimal_places=2, default=0.75, help_text='Recargo extra cuando la ubicación cae en Tena o más allá.', max_digits=8),
        ),
    ]
