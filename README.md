Ricas Papas Mary - Proyecto Django

Scaffolding inicial con apps: usuarios, productos, pedidos, pagos, reservas, entregas, insumos, proveedores, mesas, reportes y la app existente gestion_web.

## Manuales del sistema

- [Manual del usuario](MANUAL_USUARIO.md)
- [Manual del administrador](MANUAL_ADMINISTRADOR.md)
- [Manual del usuario final](MANUAL_USUARIO_FINAL.md)
- [Manual del administrador final](MANUAL_ADMINISTRADOR_FINAL.md)
- [Manual del usuario final (DOCX)](Ricas_Papas_Mary_Manual_Usuario_Final.docx)
- [Manual del administrador final (DOCX)](Ricas_Papas_Mary_Manual_Administrador_Final.docx)
- [Manual del usuario final (PDF)](Ricas_Papas_Mary_Manual_Usuario_Final.pdf)
- [Manual del administrador final (PDF)](Ricas_Papas_Mary_Manual_Administrador_Final.pdf)

Pasos para poner en marcha (desarrollo):

1. Crear y activar el entorno virtual (ya existe venv en este repo). Si no está, crear:
   python -m venv venv
   .\venv\Scripts\activate

2. Instalar dependencias:
   pip install -r requirements.txt

3. Aplicar migraciones:
   .\venv\Scripts\python.exe manage.py makemigrations
   .\venv\Scripts\python.exe manage.py migrate

4. Crear superusuario:
   .\venv\Scripts\python.exe manage.py createsuperuser

5. Ejecutar servidor de desarrollo:
   .\venv\Scripts\python.exe manage.py runserver

6. Configurar Google Maps para el checkout de domicilio:
   - Definir la variable de entorno `GOOGLE_MAPS_API_KEY` con una clave válida de Google Maps Platform.
   - El mapa de la pantalla de pago usa esa clave para cargar Google Maps y el buscador de ubicaciones.

Notas importantes:
- Este repositorio ya incluye una app monolítica `gestion_web` con modelos principales. Las nuevas apps actúan como proxies (proxy models) para evitar cambios destructivos en la base de datos.
- Para reorganizar y mover definitivamente modelos entre apps se requiere una migración manual y plan de migración de datos (puedo ayudar con eso si lo deseas).
- Para subir imágenes, asegúrate de que MEDIA_ROOT y MEDIA_URL estén configurados (ya están en core/settings.py) y que `DEBUG=True` en desarrollo.

Siguientes pasos recomendados:
- Implementar vistas y templates específicos por app.
- Agregar tests automatizados.
- Añadir integración con un servicio de envío de correos para recuperación de contraseña.

Despliegue recomendado (Render):

1. Crear una base de datos PostgreSQL en Render.
2. Crea un servicio web con la opción "Web Service" y conecta este repositorio.
3. En variables de entorno define:
   - `DEBUG=False`
   - `DJANGO_SECRET_KEY=tu_clave_larga_y_aleatoria`
   - `ALLOWED_HOSTS=localhost,127.0.0.1,tu-app.onrender.com`
   - `CSRF_TRUSTED_ORIGINS=https://tu-app.onrender.com`
   - `DATABASE_URL=postgres://...`
   - `GOOGLE_MAPS_API_KEY=tu_clave_de_google_maps`
4. Ejecuta el despliegue; Render hará la instalación, migraciones y `collectstatic`.
5. Crea el superusuario con:
   `python manage.py createsuperuser`

Si quieres que siga y genere vistas completas, formularios, endpoints y el dashboard con Chart.js ahora, dime y prosigo con la implementación detallada de cada flujo (carrito, comprobantes, validación por empleado, reportes).