from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0019_remove_configuracionsitio_imagen_fondo_inicio'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='configuracionsitio',
            name='subtitulo_inicio',
        ),
        migrations.RemoveField(
            model_name='configuracionsitio',
            name='titulo_inicio',
        ),
    ]