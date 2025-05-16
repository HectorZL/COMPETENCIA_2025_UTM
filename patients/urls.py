from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
    path('agendar-cita/', views.agendar_cita_view, name='agendar_cita'),
    path('editar-cita/', views.editar_cita, name='editar_cita'),
    path('cancelar-cita/<int:id>/', views.cancelar_cita, name='cancelar_cita'),
    path('api/horarios-disponibles/', views.obtener_horarios_disponibles, name='horarios_disponibles'),
    path('agregar-horario/', views.agregar_horario, name='agregar_horario'),
    path('agregar-horario-view/', views.agregarHorarioView, name='agregar_horario_view'),
    path('editar-horario/', views.editar_horario, name='editar_horario'),
    path('eliminar-horario/<int:id>/', views.eliminar_horario, name='eliminar_horario'),
    path('', views.patients, name='patients'),
    path('<int:id>/', views.patient_view, name='patient_view'),
    path('delete_consult/<int:id>/', views.delete_consult, name='delete_consult'),
    path('public_consult/<int:id>/', views.public_consult, name='public_consult'),
    path('doctor-report/', views.generate_doctor_report, name='doctor_report'),
    path('patient-report/', views.generate_patient_report, name='patient_report'),
]
