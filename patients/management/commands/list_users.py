from django.core.management.base import BaseCommand
from patients.models import Medico, Paciente

class Command(BaseCommand):
    help = 'Lista todos los médicos y pacientes registrados'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Médicos registrados:'))
        for medico in Medico.objects.all():
            self.stdout.write(f"ID: {medico.MedicoID}, Nombre: {medico.Nombre}, Email: {medico.Email}")
        
        self.stdout.write("\n" + self.style.SUCCESS('Pacientes registrados:'))
        for paciente in Paciente.objects.all():
            self.stdout.write(f"ID: {paciente.PacienteID}, Nombre: {paciente.Nombre}, Email: {paciente.Email}") 