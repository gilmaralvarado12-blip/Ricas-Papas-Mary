from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0016_configuracionsitio_mostrar_seccion_destacados_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracionsitio',
            name='enlace_boton_principal_hero',
            field=models.CharField(default='/menu/', help_text='Enlace del boton principal del hero. Puedes usar rutas relativas como /menu/.', max_length=255),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='enlace_boton_secundario_hero',
            field=models.CharField(default='/registro/', help_text='Enlace del boton secundario del hero. Puedes usar rutas relativas como /registro/.', max_length=255),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='etiqueta_seccion_destacados',
            field=models.CharField(default='Seleccion destacada', help_text='Texto corto mostrado arriba del titulo de la seccion destacada.', max_length=80),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='subtitulo_logo',
            field=models.CharField(default='Rukullacta', help_text='Texto pequeño mostrado debajo del nombre principal del logo.', max_length=80),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='texto_boton_principal_hero',
            field=models.CharField(default='Explorar pedidos', help_text='Texto del boton principal del hero.', max_length=80),
        ),
        migrations.AddField(
            model_name='configuracionsitio',
            name='texto_boton_secundario_hero',
            field=models.CharField(default='Crear cuenta', help_text='Texto del boton secundario del hero.', max_length=80),
        ),
    ]