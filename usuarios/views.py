from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PerfilClienteForm, UsuarioAdminCreateForm, UsuarioAdminUpdateForm

Usuario = get_user_model()


def _es_admin_o_empleado(user):
	try:
		return user.is_authenticated and user.rol in ('ADMIN', 'EMPLEADO')
	except Exception:
		return False


def _es_admin(user):
	try:
		return user.is_authenticated and user.rol == 'ADMIN'
	except Exception:
		return False


@login_required
def mi_perfil(request):
	# Cliente/usuario actualiza sus datos personales con validaciones de correo y teléfono.
	if request.method == 'POST':
		form = PerfilClienteForm(request.POST, instance=request.user)
		if form.is_valid():
			form.save()
			messages.success(request, 'Tu perfil se actualizó correctamente.')
			return redirect('usuarios:mi_perfil')
	else:
		form = PerfilClienteForm(instance=request.user)
	return render(request, 'usuarios/mi_perfil.html', {'form': form})


@login_required
@user_passes_test(_es_admin_o_empleado)
def lista_usuarios(request):
	usuarios = Usuario.objects.all().order_by('username')
	return render(request, 'usuarios/lista_usuarios.html', {'usuarios': usuarios})


@login_required
@user_passes_test(_es_admin)
def crear_usuario(request):
	# CRUD - Create para personal interno.
	if request.method == 'POST':
		form = UsuarioAdminCreateForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Usuario creado correctamente.')
			return redirect('usuarios:lista_usuarios')
	else:
		form = UsuarioAdminCreateForm()
	return render(request, 'usuarios/form_usuario.html', {'form': form, 'titulo': 'Crear usuario'})


@login_required
@user_passes_test(_es_admin)
def editar_usuario(request, usuario_id):
	usuario = get_object_or_404(Usuario, pk=usuario_id)
	if request.method == 'POST':
		form = UsuarioAdminUpdateForm(request.POST, instance=usuario)
		if form.is_valid():
			form.save()
			messages.success(request, 'Usuario actualizado correctamente.')
			return redirect('usuarios:lista_usuarios')
	else:
		form = UsuarioAdminUpdateForm(instance=usuario)
	return render(request, 'usuarios/form_usuario.html', {
		'form': form,
		'titulo': f'Editar usuario: {usuario.username}',
		'usuario_obj': usuario,
	})


@login_required
@user_passes_test(_es_admin)
def eliminar_usuario(request, usuario_id):
	usuario = get_object_or_404(Usuario, pk=usuario_id)

	# Evitamos eliminar al propio usuario logueado para no romper sesión en curso.
	if usuario.pk == request.user.pk:
		messages.error(request, 'No puedes eliminar tu propio usuario mientras estás en sesión.')
		return redirect('usuarios:lista_usuarios')

	if request.method == 'POST':
		username = usuario.username
		usuario.delete()
		messages.success(request, f'Usuario {username} eliminado correctamente.')
		return redirect('usuarios:lista_usuarios')

	return render(request, 'usuarios/confirmar_eliminar_usuario.html', {'usuario_obj': usuario})
