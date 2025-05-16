from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Medico, Paciente, Cita, HistoriaClinica, HorarioMedico
from django.contrib import messages
from django.contrib.messages import constants
from django.urls import reverse
from django.db.models import Count, Q

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


        try:
            user = Medico.objects.get(Email=email)
            if user.check_password(password):
                request.session['user_id'] = user.MedicoID
                request.session['user_type'] = 'Medico'
                request.session['user_name'] = user.Nombre
                messages.add_message(request, constants.SUCCESS, 'Login exitoso!')
                return redirect('dashboard')
            else:
                messages.add_message(request, constants.ERROR, 'Contraseña incorrecta!')
        except Medico.DoesNotExist:

                try:
                    user = Paciente.objects.get(Email=email)
                    if user.check_password(password):
                        request.session['user_id'] = user.PacienteID
                        request.session['user_type'] = 'Paciente'
                        request.session['user_name'] = user.Nombre
                        messages.add_message(request, constants.SUCCESS, 'Login exitoso!')
                        return redirect('dashboard')
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
def dashboard_view(request):
    """
    Vista del dashboard que muestra diferentes secciones según el rol del usuario
    """
    context = {}
    
    # Fecha actual para filtros
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    if request.session.get('user_type') == 'Medico':
        medico_id = request.session.get('user_id')
        medico = Medico.objects.get(MedicoID=medico_id)
        
        # Horarios del médico
        horarios = HorarioMedico.objects.filter(MedicoID=medico)
        
        # Citas del médico
        citas = Cita.objects.filter(MedicoID=medico).order_by('FechaCita', 'HoraCita')
        
        # Estadísticas
        citas_pendientes = citas.filter(FechaCita__gte=hoy, Estado='Pendiente').count()
        citas_hoy = citas.filter(FechaCita=hoy).count()
        total_pacientes = Paciente.objects.filter(cita__MedicoID=medico).distinct().count()
        consultas_mes = citas.filter(FechaCita__gte=primer_dia_mes, Estado='Completada').count()
        
        context = {
            'horarios': horarios,
            'citas': citas,
            'citas_pendientes': citas_pendientes,
            'citas_hoy': citas_hoy,
            'total_pacientes': total_pacientes,
            'consultas_mes': consultas_mes
        }
        
    else:  # Paciente
        paciente_id = request.session.get('user_id')
        paciente = Paciente.objects.get(PacienteID=paciente_id)
        
        # Lista de médicos para agendar cita
        medicos = Medico.objects.all()
        
        # Citas del paciente
        citas = Cita.objects.filter(PacienteID=paciente).order_by('FechaCita', 'HoraCita')
        
        # Historia clínica
        historias = HistoriaClinica.objects.filter(PacienteID=paciente).order_by('-FechaConsulta')
        
        # Estadísticas
        citas_pendientes = citas.filter(FechaCita__gte=hoy).exclude(Estado='Cancelada').count()
        proxima_cita = citas.filter(FechaCita__gte=hoy).exclude(Estado='Cancelada').order_by('FechaCita', 'HoraCita').first()
        total_consultas = historias.count()
        
        context = {
            'medicos': medicos,
            'citas': citas,
            'historias': historias,
            'citas_pendientes': citas_pendientes,
            'proxima_cita': proxima_cita,
            'total_consultas': total_consultas
        }
    
    return render(request, 'dashboard.html', context)

@login_required
def agendar_cita_view(request):
    """
    Vista para agendar una cita
    """
    if request.session.get('user_type') != 'Paciente':
        messages.add_message(request, constants.ERROR, 'Solo los pacientes pueden agendar citas')
        return redirect('dashboard')
    
    if request.method == 'POST':
        paciente_id = request.session.get('user_id')
        paciente = Paciente.objects.get(PacienteID=paciente_id)
        medico_id = request.POST.get('medico')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        tipo = request.POST.get('tipo')
        
        # Validar que la fecha y hora sean futuras
        fecha_hora_cita = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        if fecha_hora_cita < datetime.now():
            messages.add_message(request, constants.ERROR, 'La fecha y hora deben ser futuras')
            return redirect('dashboard')
        
        # Validar disponibilidad del médico
        try:
            medico = Medico.objects.get(MedicoID=medico_id)
            
            # Verificar si el médico tiene horario para ese día
            dia_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][datetime.strptime(fecha, "%Y-%m-%d").weekday()]
            
            horario = HorarioMedico.objects.filter(
                MedicoID=medico,
                DiaSemana=dia_semana,
                HoraInicio__lte=hora,
                HoraFin__gte=hora
            ).first()
            
            if not horario:
                messages.add_message(request, constants.ERROR, 'El médico no tiene disponibilidad en el horario seleccionado')
                return redirect('dashboard')
            
            # Verificar si ya existe una cita en ese horario
            cita_existente = Cita.objects.filter(
                MedicoID=medico,
                FechaCita=fecha,
                HoraCita=hora
            ).exclude(Estado='Cancelada').first()
            
            if cita_existente:
                messages.add_message(request, constants.ERROR, 'Ya existe una cita en ese horario')
                return redirect('dashboard')
            
            # Crear la cita
            cita = Cita(
                MedicoID=medico,
                PacienteID=paciente,
                FechaCita=fecha,
                HoraCita=hora,
                MedioCita=tipo,
                Estado='Pendiente'
            )
            cita.save()
            
            messages.add_message(request, constants.SUCCESS, 'Cita agendada exitosamente')
            return redirect('dashboard')
            
        except Medico.DoesNotExist:
            messages.add_message(request, constants.ERROR, 'El médico no existe')
            
    return redirect('dashboard')
def agregarHorarioView(request):
    return render(request, 'agregarHorarios.html')
@login_required
def agregarHorario(request):
    id = request.session.get('user_id')
    medico_id = Medico.objects.get(MedicoID=id)
    fecha = request.POST.get('fecha')
    hora_inicio = request.POST.get('hora-inicio')
    hora_final = request.POST.get('hora-final')
    Horario = HorarioMedico(
        MedicoID=medico_id,
        DiaSemana=fecha,
        HoraInicio=hora_inicio,
        HoraFin=hora_final,
    )
    Horario.save()
    return redirect('dashboard')




@login_required
def obtener_horarios_disponibles(request):
    """
    API para obtener los horarios disponibles de un médico en una fecha específica
    """
    medico_id = request.GET.get('medico_id')
    fecha = request.GET.get('fecha')
    
    if not medico_id or not fecha:
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)
    
    try:
        medico = Medico.objects.get(MedicoID=medico_id)
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        # Obtener el día de la semana
        dia_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][fecha_obj.weekday()]
        
        # Obtener horarios del médico para ese día
        horarios = HorarioMedico.objects.filter(MedicoID=medico, DiaSemana=dia_semana)
        
        # Obtener citas ya agendadas para ese día
        citas_agendadas = Cita.objects.filter(
            MedicoID=medico,
            FechaCita=fecha,
        ).exclude(Estado='Cancelada').values_list('HoraCita', flat=True)
        
        # Generar horarios disponibles (intervalos de 30 min)
        horarios_disponibles = []
        
        for horario in horarios:
            hora_inicio = datetime.strptime(str(horario.HoraInicio), "%H:%M:%S").time()
            hora_fin = datetime.strptime(str(horario.HoraFin), "%H:%M:%S").time()
            
            hora_actual = datetime.combine(datetime.today(), hora_inicio)
            while hora_actual.time() < hora_fin:
                hora_str = hora_actual.strftime("%H:%M")
                # Verificar si la hora ya está agendada
                if hora_actual.time() not in citas_agendadas:
                    horarios_disponibles.append({
                        'hora': hora_str,
                        'label': hora_str
                    })
                hora_actual += timedelta(minutes=30)
        
        return JsonResponse({'horarios': horarios_disponibles})
        
    except Medico.DoesNotExist:
        return JsonResponse({'error': 'Médico no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
