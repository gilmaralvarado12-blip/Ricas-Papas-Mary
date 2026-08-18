from django.core.management.base import BaseCommand
from gestion_web.models import Pedido
from datetime import datetime

class Command(BaseCommand):
    help = "Genera un reporte de pedidos del día"

    def handle(self, *args, **kwargs):
        hoy = datetime.today().date()
        pedidos = Pedido.objects.filter(fecha_creacion__date=hoy)

        reporte = f"Reporte de pedidos {hoy}\n"
        for pedido in pedidos:
            reporte += f"- {pedido.id} | Cliente: {pedido.cliente} | Total: {pedido.total}\n"

        # Guardar en archivo
        with open(f"reporte_{hoy}.txt", "w", encoding="utf-8") as f:
            f.write(reporte)

        self.stdout.write(self.style.SUCCESS("Reporte generado correctamente"))
