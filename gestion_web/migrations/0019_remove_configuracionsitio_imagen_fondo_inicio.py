from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0018_configuracionsitio_fondo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='configuracionsitio',
            name='imagen_fondo_inicio',
        ),
    ]