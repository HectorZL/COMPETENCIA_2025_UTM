from django.db import models
from django.urls import reverse
from django.contrib.auth.hashers import make_password, check_password

class Medico(models.Model):
    MedicoID = models.AutoField(primary_key=True)
    Nombre = models.CharField(max_length=255)
    Especialidad = models.CharField(max_length=100, blank=True, null=True)
    Email = models.EmailField(unique=True)
    Telefono = models.CharField(max_length=20, blank=True, null=True)
    Password = models.CharField(max_length=128)  # Campo para la contraseña

    def __str__(self):
        return self.Nombre
    
    def set_password(self, raw_password):
        self.Password = make_password(raw_password)
        
    def check_password(self, raw_password):
        return check_password(raw_password, self.Password)

class HorarioMedico(models.Model):
    HorarioID = models.AutoField(primary_key=True)
    MedicoID = models.ForeignKey(Medico, on_delete=models.CASCADE)
    DiaSemana = models.CharField(
        max_length=10,
        choices=[
            ('Lunes', 'Lunes'),
            ('Martes', 'Martes'),
            ('Miércoles', 'Miércoles'),
            ('Jueves', 'Jueves'),
            ('Viernes', 'Viernes'),
            ('Sábado', 'Sábado'),
            ('Domingo', 'Domingo'),
        ]
    )
    HoraInicio = models.TimeField()
    HoraFin = models.TimeField()

    class Meta:
        unique_together = ('MedicoID', 'DiaSemana', 'HoraInicio') # Evita horarios duplicados

    def __str__(self):
        return f"{self.MedicoID.Nombre} - {self.DiaSemana} ({self.HoraInicio}-{self.HoraFin})"

class Paciente(models.Model):
    PacienteID = models.AutoField(primary_key=True)
    Nombre = models.CharField(max_length=255)
    FechaNacimiento = models.DateField(blank=True, null=True)
    Genero = models.CharField(
        max_length=10,
        choices=[
            ('Masculino', 'Masculino'),
            ('Femenino', 'Femenino'),
            ('Otro', 'Otro'),
        ],
        blank=True,
        null=True
    )
    Email = models.EmailField(unique=True)
    Telefono = models.CharField(max_length=20, blank=True, null=True)
    Password = models.CharField(max_length=128)  # Campo para la contraseña
    TipoUsuario = models.CharField(
        max_length=10,
        choices=[
            ('Paciente', 'Paciente'),
            ('Medico', 'Medico'),
        ],
        default='Paciente'
    )

    def __str__(self):
        return self.Nombre
        
    def set_password(self, raw_password):
        self.Password = make_password(raw_password)
        
    def check_password(self, raw_password):
        return check_password(raw_password, self.Password)

class Cita(models.Model):
    CitaID = models.AutoField(primary_key=True)
    MedicoID = models.ForeignKey(Medico, on_delete=models.CASCADE)
    PacienteID = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    FechaCita = models.DateField()
    HoraCita = models.TimeField()
    MedioCita = models.CharField(
        max_length=10,
        choices=[
            ('Presencial', 'Presencial'),
            ('Virtual', 'Virtual'),
        ]
    )
    Estado = models.CharField(
        max_length=10,
        choices=[
            ('Pendiente', 'Pendiente'),
            ('Confirmada', 'Confirmada'),
            ('Cancelada', 'Cancelada'),
            ('Completada', 'Completada'),
        ],
        default='Pendiente'
    )
    FechaCreacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('MedicoID', 'FechaCita', 'HoraCita') # Evita citas duplicadas

    def __str__(self):
        return f"Cita {self.CitaID} - {self.PacienteID.Nombre} con {self.MedicoID.Nombre} el {self.FechaCita} a las {self.HoraCita}"

class HistoriaClinica(models.Model):
    HistoriaID = models.AutoField(primary_key=True)
    PacienteID = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    FechaConsulta = models.DateTimeField(auto_now_add=True)
    Diagnostico = models.TextField(blank=True, null=True)
    Tratamiento = models.TextField(blank=True, null=True)
    NotasAdicionales = models.TextField(blank=True, null=True)
    MedicoID = models.ForeignKey(Medico, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"Historia Clínica de {self.PacienteID.Nombre} - {self.FechaConsulta}"