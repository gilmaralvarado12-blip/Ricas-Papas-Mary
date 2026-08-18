from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0014_configuracionsitio_subtitulo_inicio_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracionsitio',
            name='logo_principal',
            field=models.ImageField(blank=True, help_text='Logo principal mostrado en el encabezado de la portada.', null=True, upload_to='logos/'),
        ),
        migrations.AddField(
            model_name='platodestacadoportada',
            name='descripcion_corta',
            field=models.CharField(blank=True, help_text='Descripcion breve opcional mostrada debajo del nombre del plato.', max_length=180),
        ),
    ]