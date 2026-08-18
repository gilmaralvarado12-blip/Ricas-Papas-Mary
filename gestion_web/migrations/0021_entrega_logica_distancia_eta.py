from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0020_remove_configuracionsitio_subtitulo_inicio_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='entrega',
            name='cargo_adicional',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=7),
        ),
        migrations.AddField(
            model_name='entrega',
            name='distancia_km',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True),
        ),
        migrations.AddField(
            model_name='entrega',
            name='fuera_rango_estandar',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='entrega',
            name='tiempo_estimado_minutos',
            field=models.PositiveIntegerField(default=30),
        ),
    ]
