from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0015_configuracionsitio_logo_principal_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracionsitio',
            name='mostrar_seccion_destacados',
            field=models.BooleanField(default=True, help_text='Activa o desactiva la seccion de platos destacados en la portada.'),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='subtitulo_seccion_destacados',
            field=models.TextField(default='Descubre una muestra del menu con opciones listas para agregar al carrito o revisar dentro del sistema.', help_text='Texto secundario de la seccion de platos destacados.'),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='titulo_seccion_destacados',
            field=models.CharField(default='Platos favoritos para empezar tu pedido', help_text='Titulo principal de la seccion de platos destacados.', max_length=180),
        ),
    ]