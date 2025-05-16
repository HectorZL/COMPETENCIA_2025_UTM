from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('agregar-horario-redirect/', views.agregarHorarioView, name='agregar_horario_view'),
    path('agregar-horario/', views.agregarHorario, name='agregar_horario'),
    path('agendar-cita/', views.agendar_cita_view, name='agendar_cita'),
    path('api/horarios-disponibles/', views.obtener_horarios_disponibles, name='horarios_disponibles'),
    path('', views.patients, name='patients'),
    path('<int:id>/', views.patient_view, name='patient_view'),
    path('delete_consult/<int:id>/', views.delete_consult, name='delete_consult'),
    path('public_consult/<int:id>/', views.public_consult, name='public_consult'),
]
