from django.db import migrations, models


def set_estado_from_disponible(apps, schema_editor):
    """Inicializa estado de mesa a partir del campo legado `disponible`."""
    Mesa = apps.get_model('gestion_web', 'Mesa')
    for mesa in Mesa.objects.all():
        mesa.estado = 'DISPONIBLE' if mesa.disponible else 'OCUPADA'
        mesa.save(update_fields=['estado'])


def set_disponible_from_estado(apps, schema_editor):
    """Rollback: vuelve a derivar `disponible` desde `estado`."""
    Mesa = apps.get_model('gestion_web', 'Mesa')
    for mesa in Mesa.objects.all():
        mesa.disponible = mesa.estado == 'DISPONIBLE'
        mesa.save(update_fields=['disponible'])


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_web', '0006_alter_pedido_estado_alter_usuario_rol'),
    ]

    operations = [
        migrations.AddField(
            model_name='mesa',
            name='estado',
            field=models.CharField(
                choices=[
                    ('DISPONIBLE', 'Disponible'),
                    ('OCUPADA', 'Ocupada'),
                    ('MANTENIMIENTO', 'Mantenimiento'),
                ],
                default='DISPONIBLE',
                max_length=20,
            ),
        ),
        migrations.RunPython(set_estado_from_disponible, set_disponible_from_estado),
    ]
