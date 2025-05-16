from .models import Medico, Paciente

def set_password_for_medico(email, password):
    """
    Función para establecer una contraseña para un médico
    """
    try:
        medico = Medico.objects.get(Email=email)
        medico.set_password(password)
        medico.save()
        return True, f"Contraseña actualizada para {medico.Nombre}"
    except Medico.DoesNotExist:
        return False, f"No se encontró ningún médico con el email {email}"

def set_password_for_paciente(email, password):
    """
    Función para establecer una contraseña para un paciente
    """
    try:
        paciente = Paciente.objects.get(Email=email)
        paciente.set_password(password)
        paciente.save()
        return True, f"Contraseña actualizada para {paciente.Nombre}"
    except Paciente.DoesNotExist:
        return False, f"No se encontró ningún paciente con el email {email}" 