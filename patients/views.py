from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Medico, Paciente, Cita, HistoriaClinica, HorarioMedico
from django.contrib import messages
from django.contrib.messages import constants
from django.urls import reverse
from django.db.models import Count, Q
import re

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

def register_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        genero = request.POST.get('genero')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        password = request.POST.get('password')
        
        # Validaciones
        if not nombre or not email or not telefono or not password:
            messages.add_message(request, constants.ERROR, 'Todos los campos marcados son obligatorios')
            return redirect('register')
        
        # Validar formato de teléfono (debe comenzar con 09 y tener 10 dígitos)
        if not re.match(r'^09\d{8}$', telefono):
            messages.add_message(request, constants.ERROR, 'El número de teléfono debe comenzar con 09 y tener 10 dígitos')
            return redirect('register')
        
        # Verificar si el correo ya existe
        if Paciente.objects.filter(Email=email).exists() or Medico.objects.filter(Email=email).exists():
            messages.add_message(request, constants.ERROR, 'El correo electrónico ya está registrado')
            return redirect('register')
        
        # Crear el paciente
        paciente = Paciente(
            Nombre=nombre,
            Email=email,
            Telefono=telefono,
            Genero=genero,
            TipoUsuario='Paciente'
        )
        
        # Añadir fecha de nacimiento si está presente
        if fecha_nacimiento:
            paciente.FechaNacimiento = fecha_nacimiento
        
        # Establecer contraseña
        paciente.set_password(password)
        paciente.save()
        
        messages.add_message(request, constants.SUCCESS, 'Registro exitoso! Ahora puedes iniciar sesión')
        return redirect('login')
    
    # Si es GET, mostrar el formulario de registro
    return render(request, 'register.html')

def logout_view(request):
    """
    Vista para confirmar y realizar el cierre de sesión
    """
    if request.method == 'POST':
        # Si es POST, se confirma el cierre de sesión
        if 'user_id' in request.session:
            del request.session['user_id']
            del request.session['user_type']
            del request.session['user_name']
        messages.add_message(request, constants.SUCCESS, 'Has cerrado sesión exitosamente')
        return redirect('login')
    else:
        # Si es GET, mostrar la página de confirmación
        return render(request, 'logout.html')

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
    cita_id = request.GET.get('cita_id', None)  # Para excluir la cita actual al editar
    
    if not medico_id or not fecha:
        return JsonResponse({'error': 'Parámetros incompletos'}, status=400)
    
    try:
        medico = Medico.objects.get(MedicoID=medico_id)
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        # Obtener el día de la semana
        dia_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][fecha_obj.weekday()]
        
        # Obtener horarios del médico para ese día
        horarios = HorarioMedico.objects.filter(MedicoID=medico, DiaSemana=dia_semana)
        
        # Obtener citas ya agendadas para ese día (excluyendo la cita que se está editando)
        citas_filter = Q(MedicoID=medico, FechaCita=fecha) & ~Q(Estado='Cancelada')
        if cita_id:
            citas_filter &= ~Q(CitaID=cita_id)
            
        citas_agendadas = Cita.objects.filter(citas_filter).values_list('HoraCita', flat=True)
        
        # Generar horarios disponibles (por horas completas, no intervalos de 30 min)
        horarios_disponibles = []
        
        for horario in horarios:
            hora_inicio = datetime.strptime(str(horario.HoraInicio), "%H:%M:%S").time()
            hora_fin = datetime.strptime(str(horario.HoraFin), "%H:%M:%S").time()
            
            # Usar horas completas en lugar de intervalos de 30 minutos
            for hora in range(hora_inicio.hour, hora_fin.hour):
                hora_str = f"{hora:02d}:00"
                hora_obj = datetime.strptime(hora_str, "%H:%M").time()
                
                # Verificar si la hora ya está agendada
                if hora_obj not in citas_agendadas:
                    # Formato más amigable para mostrar (7 en lugar de 07:00)
                    horarios_disponibles.append({
                        'hora': hora_str,
                        'label': f"{hora}"
                    })
        
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

@login_required
def edit_profile_view(request):
    """
    Vista para editar el perfil del usuario (médico o paciente)
    """
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    # Obtener el usuario actual según su tipo
    if user_type == 'Medico':
        user = Medico.objects.get(MedicoID=user_id)
        is_doctor = True
    else:
        user = Paciente.objects.get(PacienteID=user_id)
        is_doctor = False
    
    if request.method == 'POST':
        # Datos comunes para ambos tipos de usuario
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        password = request.POST.get('password')
        
        # Validaciones básicas
        if not nombre or not email or not telefono:
            messages.add_message(request, constants.ERROR, 'Todos los campos marcados son obligatorios')
            return redirect('edit_profile')
        
        # Validar que el email no esté en uso por otro usuario
        if is_doctor:
            email_exists = Medico.objects.filter(Email=email).exclude(MedicoID=user_id).exists() or \
                           Paciente.objects.filter(Email=email).exists()
        else:
            email_exists = Paciente.objects.filter(Email=email).exclude(PacienteID=user_id).exists() or \
                           Medico.objects.filter(Email=email).exists()
        
        if email_exists:
            messages.add_message(request, constants.ERROR, 'El correo electrónico ya está registrado')
            return redirect('edit_profile')
        
        # Validar formato de teléfono (debe comenzar con 09 y tener 10 dígitos)
        if telefono and not re.match(r'^09\d{8}$', telefono):
            messages.add_message(request, constants.ERROR, 'El número de teléfono debe comenzar con 09 y tener 10 dígitos')
            return redirect('edit_profile')
        
        # Actualizar datos comunes
        user.Nombre = nombre
        user.Email = email
        user.Telefono = telefono
        
        # Actualizar contraseña si se proporciona
        if password:
            user.set_password(password)
        
        # Datos específicos para médicos o pacientes
        if is_doctor:
            especialidad = request.POST.get('especialidad')
            if especialidad:
                user.Especialidad = especialidad
        else:
            genero = request.POST.get('genero')
            fecha_nacimiento = request.POST.get('fecha_nacimiento')
            
            if genero:
                user.Genero = genero
            if fecha_nacimiento:
                user.FechaNacimiento = fecha_nacimiento
        
        # Guardar cambios
        user.save()
        
        # Actualizar el nombre en la sesión
        request.session['user_name'] = user.Nombre
        
        messages.add_message(request, constants.SUCCESS, 'Perfil actualizado con éxito')
        return redirect('dashboard')
    
    # Para solicitudes GET, mostrar el formulario con los datos actuales
    context = {
        'user': user,
        'is_doctor': is_doctor
    }
    
    return render(request, 'edit_profile.html', context)

@login_required
def agregar_horario(request):
    """
    Vista para que el médico agregue un nuevo horario de disponibilidad
    """
    if request.session.get('user_type') != 'Medico':
        messages.add_message(request, constants.ERROR, 'Solo los médicos pueden gestionar horarios')
        return redirect('dashboard')
    
    if request.method == 'POST':
        medico_id = request.session.get('user_id')
        medico = Medico.objects.get(MedicoID=medico_id)
        dia = request.POST.get('dia')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fin = request.POST.get('hora_fin')
        
        # Validaciones
        if not dia or not hora_inicio or not hora_fin:
            messages.add_message(request, constants.ERROR, 'Todos los campos son obligatorios')
            return redirect('dashboard')
        
        # Validar que la hora de fin sea posterior a la hora de inicio
        if hora_inicio >= hora_fin:
            messages.add_message(request, constants.ERROR, 'La hora de fin debe ser posterior a la hora de inicio')
            return redirect('dashboard')
        
        # Verificar si ya existe un horario que se solape
        horarios_solapados = HorarioMedico.objects.filter(
            MedicoID=medico,
            DiaSemana=dia
        ).filter(
            Q(HoraInicio__lt=hora_fin) & Q(HoraFin__gt=hora_inicio)
        )
        
        if horarios_solapados.exists():
            messages.add_message(request, constants.ERROR, 'Ya tienes un horario que se solapa con este período')
            return redirect('dashboard')
        
        # Crear el horario
        horario = HorarioMedico(
            MedicoID=medico,
            DiaSemana=dia,
            HoraInicio=hora_inicio,
            HoraFin=hora_fin
        )
        horario.save()
        
        messages.add_message(request, constants.SUCCESS, 'Horario agregado exitosamente')
    
    return redirect('dashboard')

@login_required
def editar_horario(request):
    """
    Vista para que el médico edite un horario existente
    """
    if request.session.get('user_type') != 'Medico':
        messages.add_message(request, constants.ERROR, 'Solo los médicos pueden gestionar horarios')
        return redirect('dashboard')
    
    if request.method == 'POST':
        medico_id = request.session.get('user_id')
        medico = Medico.objects.get(MedicoID=medico_id)
        horario_id = request.POST.get('horario_id')
        dia = request.POST.get('dia')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fin = request.POST.get('hora_fin')
        
        # Validaciones
        if not horario_id or not dia or not hora_inicio or not hora_fin:
            messages.add_message(request, constants.ERROR, 'Todos los campos son obligatorios')
            return redirect('dashboard')
        
        # Validar que la hora de fin sea posterior a la hora de inicio
        if hora_inicio >= hora_fin:
            messages.add_message(request, constants.ERROR, 'La hora de fin debe ser posterior a la hora de inicio')
            return redirect('dashboard')
        
        try:
            # Verificar que el horario pertenezca al médico
            horario = HorarioMedico.objects.get(HorarioID=horario_id, MedicoID=medico)
            
            # Verificar si hay solapamiento con otros horarios del mismo día
            horarios_solapados = HorarioMedico.objects.filter(
                MedicoID=medico,
                DiaSemana=dia
            ).filter(
                Q(HoraInicio__lt=hora_fin) & Q(HoraFin__gt=hora_inicio)
            ).exclude(HorarioID=horario_id)
            
            if horarios_solapados.exists():
                messages.add_message(request, constants.ERROR, 'Este horario se solapa con otro período ya configurado')
                return redirect('dashboard')
            
            # Actualizar el horario
            horario.DiaSemana = dia
            horario.HoraInicio = hora_inicio
            horario.HoraFin = hora_fin
            horario.save()
            
            messages.add_message(request, constants.SUCCESS, 'Horario actualizado exitosamente')
            
        except HorarioMedico.DoesNotExist:
            messages.add_message(request, constants.ERROR, 'El horario no existe o no te pertenece')
    
    return redirect('dashboard')

@login_required
def eliminar_horario(request, id):
    """
    Vista para que el médico elimine un horario existente
    """
    if request.session.get('user_type') != 'Medico':
        messages.add_message(request, constants.ERROR, 'Solo los médicos pueden gestionar horarios')
        return redirect('dashboard')
    
    try:
        medico_id = request.session.get('user_id')
        horario = HorarioMedico.objects.get(HorarioID=id, MedicoID_id=medico_id)
        
        # Verificar si hay citas asociadas a este horario
        dia_semana_map = {'Lunes': 0, 'Martes': 1, 'Miércoles': 2, 'Jueves': 3, 'Viernes': 4, 'Sábado': 5, 'Domingo': 6}
        
        # Obtener todas las citas futuras del médico
        citas_futuras = Cita.objects.filter(
            MedicoID_id=medico_id,
            FechaCita__gte=timezone.now().date(),
            Estado__in=['Pendiente', 'Confirmada']
        )
        
        # Verificar si alguna cita cae en el horario que se va a eliminar
        horario_afectado = False
        for cita in citas_futuras:
            # Obtener el día de la semana de la cita (0: lunes, 6: domingo)
            dia_cita = cita.FechaCita.weekday()
            # Verificar si la cita está en el mismo día de la semana y dentro del rango de horas
            if (dia_semana_map.get(horario.DiaSemana) == dia_cita and 
                horario.HoraInicio <= cita.HoraCita <= horario.HoraFin):
                horario_afectado = True
                break
        
        if horario_afectado:
            messages.add_message(request, constants.ERROR, 
                'No se puede eliminar este horario porque hay citas programadas. Cancela las citas primero.')
            return redirect('dashboard')
        
        # Eliminar el horario
        horario.delete()
        messages.add_message(request, constants.SUCCESS, 'Horario eliminado exitosamente')
        
    except HorarioMedico.DoesNotExist:
        messages.add_message(request, constants.ERROR, 'El horario no existe o no te pertenece')
    
    return redirect('dashboard')

@login_required
def editar_cita(request):
    """
    Vista para editar una cita existente
    """
    if request.method != 'POST':
        return redirect('dashboard')
    
    cita_id = request.POST.get('cita_id')
    medico_id = request.POST.get('medico')
    fecha = request.POST.get('fecha')
    hora = request.POST.get('hora')
    tipo = request.POST.get('tipo')
    
    try:
        # Verificar que la cita pertenece al usuario
        user_id = request.session.get('user_id')
        
        if request.session.get('user_type') == 'Paciente':
            cita = Cita.objects.get(CitaID=cita_id, PacienteID_id=user_id)
        else:
            cita = Cita.objects.get(CitaID=cita_id, MedicoID_id=user_id)
        
        # Solo permitir editar citas pendientes
        if cita.Estado != 'Pendiente':
            messages.add_message(request, constants.ERROR, 'Solo se pueden editar citas en estado pendiente')
            return redirect('dashboard')
            
        # Validar que la fecha y hora sean futuras
        fecha_hora_cita = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        if fecha_hora_cita < datetime.now():
            messages.add_message(request, constants.ERROR, 'La fecha y hora deben ser futuras')
            return redirect('dashboard')
        
        # Validar disponibilidad del médico
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
        
        # Verificar si ya existe otra cita en ese horario
        cita_existente = Cita.objects.filter(
            MedicoID=medico,
            FechaCita=fecha,
            HoraCita=hora
        ).exclude(CitaID=cita_id).exclude(Estado='Cancelada').first()
        
        if cita_existente:
            messages.add_message(request, constants.ERROR, 'Ya existe una cita en ese horario')
            return redirect('dashboard')
        
        # Actualizar la cita
        cita.MedicoID = medico
        cita.FechaCita = fecha
        cita.HoraCita = hora
        cita.MedioCita = tipo
        cita.save()
        
        messages.add_message(request, constants.SUCCESS, 'Cita actualizada exitosamente')
        
    except Cita.DoesNotExist:
        messages.add_message(request, constants.ERROR, 'La cita no existe o no tienes permiso para editarla')
    except Medico.DoesNotExist:
        messages.add_message(request, constants.ERROR, 'El médico seleccionado no existe')
    except Exception as e:
        messages.add_message(request, constants.ERROR, f'Error al actualizar la cita: {str(e)}')
    
    return redirect('dashboard')

@login_required
def cancelar_cita(request, id):
    """
    Vista para cancelar una cita
    """
    try:
        # Verificar que la cita pertenece al usuario
        user_id = request.session.get('user_id')
        
        if request.session.get('user_type') == 'Paciente':
            cita = Cita.objects.get(CitaID=id, PacienteID_id=user_id)
        else:
            cita = Cita.objects.get(CitaID=id, MedicoID_id=user_id)
        
        # Solo permitir cancelar citas pendientes
        if cita.Estado != 'Pendiente':
            messages.add_message(request, constants.ERROR, 'Solo se pueden cancelar citas en estado pendiente')
            return redirect('dashboard')
        
        # Cancelar la cita
        cita.Estado = 'Cancelada'
        cita.save()
        
        messages.add_message(request, constants.SUCCESS, 'Cita cancelada exitosamente')
        
    except Cita.DoesNotExist:
        messages.add_message(request, constants.ERROR, 'La cita no existe o no tienes permiso para cancelarla')
    
    return redirect('dashboard')

@login_required
def generate_doctor_report(request):
    """
    Genera un reporte para médicos sobre asistencia y cancelación de citas
    """
    if request.session.get('user_type') != 'Medico':
        messages.add_message(request, constants.ERROR, 'Acceso denegado: solo médicos pueden ver este reporte')
        return redirect('dashboard')
    
    medico_id = request.session.get('user_id')
    medico = Medico.objects.get(MedicoID=medico_id)
    
    # Fechas para filtros
    hoy = timezone.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    hace_90_dias = hoy - timedelta(days=90)
    
    # Citas del último mes
    citas_ultimo_mes = Cita.objects.filter(
        MedicoID=medico,
        FechaCita__gte=hace_30_dias,
        FechaCita__lte=hoy
    )
    
    # Citas del último trimestre
    citas_ultimo_trimestre = Cita.objects.filter(
        MedicoID=medico,
        FechaCita__gte=hace_90_dias,
        FechaCita__lte=hoy
    )
    
    # Estadísticas de asistencia y cancelación
    stats_mes = {
        'total': citas_ultimo_mes.count(),
        'completadas': citas_ultimo_mes.filter(Estado='Completada').count(),
        'canceladas': citas_ultimo_mes.filter(Estado='Cancelada').count(),
        'pendientes': citas_ultimo_mes.filter(Estado='Pendiente').count(),
        'confirmadas': citas_ultimo_mes.filter(Estado='Confirmada').count(),
    }
    
    stats_trimestre = {
        'total': citas_ultimo_trimestre.count(),
        'completadas': citas_ultimo_trimestre.filter(Estado='Completada').count(),
        'canceladas': citas_ultimo_trimestre.filter(Estado='Cancelada').count(),
        'pendientes': citas_ultimo_trimestre.filter(Estado='Pendiente').count(),
        'confirmadas': citas_ultimo_trimestre.filter(Estado='Confirmada').count(),
    }
    
    # Estadísticas por día de la semana
    citas_por_dia = {}
    for dia in ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']:
        dia_index = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'].index(dia)
        citas_por_dia[dia] = {
            'total': citas_ultimo_trimestre.filter(FechaCita__week_day=((dia_index + 2) % 7) or 7).count(),
            'canceladas': citas_ultimo_trimestre.filter(
                FechaCita__week_day=((dia_index + 2) % 7) or 7, 
                Estado='Cancelada'
            ).count()
        }
    
    # Pacientes más frecuentes
    pacientes_frecuentes = Paciente.objects.filter(
        cita__MedicoID=medico,
        cita__FechaCita__gte=hace_90_dias
    ).annotate(
        num_citas=Count('cita')
    ).order_by('-num_citas')[:5]
    
    context = {
        'medico': medico,
        'stats_mes': stats_mes,
        'stats_trimestre': stats_trimestre,
        'citas_por_dia': citas_por_dia,
        'pacientes_frecuentes': pacientes_frecuentes,
        'periodo_inicio': hace_90_dias,
        'periodo_fin': hoy
    }
    
    return render(request, 'doctor_report.html', context)

@login_required
def generate_patient_report(request):
    """
    Genera un reporte para pacientes sobre sus consultas médicas
    """
    if request.session.get('user_type') != 'Paciente':
        messages.add_message(request, constants.ERROR, 'Acceso denegado: solo pacientes pueden ver este reporte')
        return redirect('dashboard')
    
    paciente_id = request.session.get('user_id')
    paciente = Paciente.objects.get(PacienteID=paciente_id)
    
    # Fechas para filtros
    hoy = timezone.now().date()
    hace_90_dias = hoy - timedelta(days=90)
    hace_365_dias = hoy - timedelta(days=365)
    
    # Citas del último trimestre
    citas_ultimo_trimestre = Cita.objects.filter(
        PacienteID=paciente,
        FechaCita__gte=hace_90_dias,
        FechaCita__lte=hoy
    ).order_by('FechaCita')
    
    # Citas del último año
    citas_ultimo_anio = Cita.objects.filter(
        PacienteID=paciente,
        FechaCita__gte=hace_365_dias,
        FechaCita__lte=hoy
    )
    
    # Estadísticas de asistencia y cancelación
    stats_trimestre = {
        'total': citas_ultimo_trimestre.count(),
        'completadas': citas_ultimo_trimestre.filter(Estado='Completada').count(),
        'canceladas': citas_ultimo_trimestre.filter(Estado='Cancelada').count(),
        'pendientes': citas_ultimo_trimestre.filter(Estado='Pendiente').count(),
        'confirmadas': citas_ultimo_trimestre.filter(Estado='Confirmada').count(),
    }
    
    stats_anio = {
        'total': citas_ultimo_anio.count(),
        'completadas': citas_ultimo_anio.filter(Estado='Completada').count(),
        'canceladas': citas_ultimo_anio.filter(Estado='Cancelada').count(),
        'pendientes': citas_ultimo_anio.filter(Estado='Pendiente').count(),
        'confirmadas': citas_ultimo_anio.filter(Estado='Confirmada').count(),
    }
    
    # Médicos consultados
    medicos_consultados = Medico.objects.filter(
        cita__PacienteID=paciente,
        cita__FechaCita__gte=hace_365_dias
    ).annotate(
        num_citas=Count('cita')
    ).order_by('-num_citas')
    
    # Historia clínica
    historias_clinicas = HistoriaClinica.objects.filter(
        PacienteID=paciente
    ).order_by('-FechaConsulta')[:10]
    
    context = {
        'paciente': paciente,
        'citas_ultimo_trimestre': citas_ultimo_trimestre,
        'stats_trimestre': stats_trimestre,
        'stats_anio': stats_anio,
        'medicos_consultados': medicos_consultados,
        'historias_clinicas': historias_clinicas,
        'periodo_inicio': hace_365_dias,
        'periodo_fin': hoy
    }
    
    return render(request, 'patient_report.html', context)
