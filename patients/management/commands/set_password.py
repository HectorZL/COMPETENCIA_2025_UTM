from django.core.management.base import BaseCommand
from patients.models import Medico, Paciente

class Command(BaseCommand):
    help = 'Establece una contraseña para un médico o paciente basado en su email'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email del usuario')
        parser.add_argument('--password', type=str, required=True, help='Nueva contraseña')
        parser.add_argument('--tipo', type=str, required=True, choices=['medico', 'paciente'], help='Tipo de usuario')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        tipo = options['tipo']

        if tipo == 'medico':
            try:
                medico = Medico.objects.get(Email=email)
                medico.set_password(password)
                medico.save()
                self.stdout.write(self.style.SUCCESS(f'Contraseña actualizada para el médico {medico.Nombre}'))
            except Medico.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No se encontró ningún médico con el email {email}'))
        else:  # tipo == 'paciente'
            try:
                paciente = Paciente.objects.get(Email=email)
                paciente.set_password(password)
                paciente.save()
                self.stdout.write(self.style.SUCCESS(f'Contraseña actualizada para el paciente {paciente.Nombre}'))
            except Paciente.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No se encontró ningún paciente con el email {email}')) 