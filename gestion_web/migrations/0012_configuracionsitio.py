from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0011_entrega_latitud_entrega_longitud_alter_usuario_rol'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracionSitio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(default='Configuracion principal', max_length=100)),
                ('imagen_fondo_inicio', models.ImageField(blank=True, help_text='Imagen usada como fondo de la portada del sistema.', null=True, upload_to='fondos/')),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuracion del sitio',
                'verbose_name_plural': 'Configuracion del sitio',
            },
        ),
    ]