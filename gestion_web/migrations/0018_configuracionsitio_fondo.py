from django.db import migrations, models


def copy_legacy_home_background_to_global(apps, schema_editor):
    ConfiguracionSitio = apps.get_model('gestion_web', 'ConfiguracionSitio')
    for config in ConfiguracionSitio.objects.all():
        if not config.fondo and config.imagen_fondo_inicio:
            config.fondo = config.imagen_fondo_inicio
            config.save(update_fields=['fondo'])


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0017_configuracionsitio_enlace_boton_principal_hero_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracionsitio',
            name='fondo',
            field=models.ImageField(blank=True, help_text='Imagen de fondo global para todo el sistema.', null=True, upload_to='fondos/'),
        ),
        migrations.RunPython(copy_legacy_home_background_to_global, migrations.RunPython.noop),
    ]