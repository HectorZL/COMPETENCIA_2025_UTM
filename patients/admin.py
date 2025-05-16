from django.contrib import admin
from .models import Medico, Paciente, Cita, HistoriaClinica, HorarioMedico
from django import forms

class MedicoForm(forms.ModelForm):
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput, required=False)
    
    class Meta:
        model = Medico
        fields = '__all__'
    
    def save(self, commit=True):
        medico = super().save(commit=False)
        if self.cleaned_data.get('password'):
            medico.set_password(self.cleaned_data['password'])
        if commit:
            medico.save()
        return medico

class MedicoAdmin(admin.ModelAdmin):
    form = MedicoForm
    list_display = ('MedicoID', 'Nombre', 'Especialidad', 'Email')
    search_fields = ('Nombre', 'Email')
    exclude = ('Password',)  # Ocultamos el campo Password en el formulario

class PacienteForm(forms.ModelForm):
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput, required=False)
    
    class Meta:
        model = Paciente
        fields = '__all__'
    
    def save(self, commit=True):
        paciente = super().save(commit=False)
        if self.cleaned_data.get('password'):
            paciente.set_password(self.cleaned_data['password'])
        if commit:
            paciente.save()
        return paciente

class PacienteAdmin(admin.ModelAdmin):
    form = PacienteForm
    list_display = ('PacienteID', 'Nombre', 'Email', 'Genero')
    search_fields = ('Nombre', 'Email')
    exclude = ('Password',)  # Ocultamos el campo Password en el formulario

class CitaAdmin(admin.ModelAdmin):
    list_display = ('CitaID', 'MedicoID', 'PacienteID', 'FechaCita', 'HoraCita', 'Estado')
    list_filter = ('Estado', 'FechaCita')

class HistoriaClinicaAdmin(admin.ModelAdmin):
    list_display = ('HistoriaID', 'PacienteID', 'MedicoID', 'FechaConsulta')
    search_fields = ('PacienteID__Nombre', 'MedicoID__Nombre')

class HorarioMedicoAdmin(admin.ModelAdmin):
    list_display = ('HorarioID', 'MedicoID', 'DiaSemana', 'HoraInicio', 'HoraFin')
    list_filter = ('DiaSemana',)

admin.site.register(Medico, MedicoAdmin)
admin.site.register(Paciente, PacienteAdmin)
admin.site.register(Cita, CitaAdmin)
admin.site.register(HistoriaClinica, HistoriaClinicaAdmin)
admin.site.register(HorarioMedico, HorarioMedicoAdmin)
