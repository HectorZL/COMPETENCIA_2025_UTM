from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from .models import Medico, Paciente, Cita, HistoriaClinica
from django.contrib import messages
from django.contrib.messages import constants
from django.urls import reverse

# Middleware para verificar autenticación
def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return HttpResponseRedirect(reverse('login'))
        return view_func(request, *args, **kwargs)
    return wrapper

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')
        
        if user_type == 'Medico':
            try:
                user = Medico.objects.get(Email=email)
                if user.check_password(password):
                    request.session['user_id'] = user.MedicoID
                    request.session['user_type'] = 'Medico'
                    request.session['user_name'] = user.Nombre
                    messages.add_message(request, constants.SUCCESS, 'Login exitoso!')
                    return redirect('patients')
                else:
                    messages.add_message(request, constants.ERROR, 'Contraseña incorrecta!')
            except Medico.DoesNotExist:
                messages.add_message(request, constants.ERROR, 'El correo no existe!')
        else:
            try:
                user = Paciente.objects.get(Email=email)
                if user.check_password(password):
                    request.session['user_id'] = user.PacienteID
                    request.session['user_type'] = 'Paciente'
                    request.session['user_name'] = user.Nombre
                    messages.add_message(request, constants.SUCCESS, 'Login exitoso!')
                    return redirect('patients')
                else:
                    messages.add_message(request, constants.ERROR, 'Contraseña incorrecta!')
            except Paciente.DoesNotExist:
                messages.add_message(request, constants.ERROR, 'El correo no existe!')
    
    return render(request, 'login.html')

def logout_view(request):
    if 'user_id' in request.session:
        del request.session['user_id']
        del request.session['user_type']
        del request.session['user_name']
    return redirect('login')

@login_required
def patients(request):
    if request.method == 'GET':
        pacientes = Paciente.objects.all()
        return render(request, 'patients.html', {'patients': pacientes})
    elif request.method == 'POST':
        nombre = request.POST['name']
        email = request.POST['email']
        telefono = request.POST['phone']
        genero = request.POST.get('gender')
        fecha_nacimiento = request.POST.get('birth_date')
        
        # Validaciones básicas
        if len(nombre.strip()) == 0 or len(email.strip()) == 0:
            messages.add_message(request, constants.ERROR, '¡Por favor complete los campos obligatorios!')
            return redirect('patients')
        
        # Crear el paciente
        paciente = Paciente(
            Nombre=nombre,
            Email=email,
            Telefono=telefono,
            Genero=genero
        )
        
        # Añadir fecha de nacimiento si está presente
        if fecha_nacimiento:
            paciente.FechaNacimiento = fecha_nacimiento
            
        # Generar una contraseña temporal
        paciente.set_password('temp123')
        paciente.save()
        
        messages.add_message(request, constants.SUCCESS, '¡Paciente registrado con éxito!')
        return redirect('patients')

@login_required
def patient_view(request, id):
    try:
        paciente = Paciente.objects.get(PacienteID=id)
        if request.method == 'GET':
            citas = Cita.objects.filter(PacienteID=paciente)
            historias = HistoriaClinica.objects.filter(PacienteID=paciente)
            
            return render(request, 'patient.html', {'patient': paciente, 'citas': citas, 'historias': historias})
        else:
            # Lógica para manejar POST
            # (Adaptaríamos según los requisitos específicos)
            messages.add_message(request, constants.SUCCESS, 'Operación realizada con éxito.')
            return redirect(f'/patients/{id}')
    except Paciente.DoesNotExist:
        raise Http404("Paciente no encontrado")

@login_required
def upgrade_patient(request, id):
    # Adaptar según las necesidades
    try:
        paciente = Paciente.objects.get(PacienteID=id)
        # Actualizar algún campo del paciente según necesidades
        paciente.save()
        return redirect(f'/patients/{id}')
    except Paciente.DoesNotExist:
        raise Http404("Paciente no encontrado")

@login_required
def delete_consult(request, id):
    # Adaptamos a nuestro modelo
    try:
        historia = HistoriaClinica.objects.get(HistoriaID=id)
        paciente_id = historia.PacienteID.PacienteID
        historia.delete()
        return redirect(f'/patients/{paciente_id}')
    except HistoriaClinica.DoesNotExist:
        raise Http404("Historia clínica no encontrada")

@login_required
def public_consult(request, id):
    # Adaptamos a nuestro modelo
    try:
        historia = HistoriaClinica.objects.get(HistoriaID=id)
        return render(request, 'public_consult.html', {'historia': historia})
    except HistoriaClinica.DoesNotExist:
        raise Http404("Historia clínica no encontrada")
