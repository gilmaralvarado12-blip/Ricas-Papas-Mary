from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0012_configuracionsitio'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracionsitio',
            name='platos_destacados',
            field=models.ManyToManyField(blank=True, help_text='Selecciona entre 3 y 5 platos destacados para la portada.', limit_choices_to={'disponible': True}, related_name='configuraciones_destacadas', to='gestion_web.producto'),
        ),
    ]