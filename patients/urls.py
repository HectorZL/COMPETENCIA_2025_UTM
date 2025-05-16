from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.patients, name='patients'),
    path('<int:id>', views.patient_view, name='patient_view'),
    path('delete_consult/<int:id>', views.delete_consult, name='delete_consult'),
    path('public_consult/<int:id>', views.public_consult, name='public_consult'),
]
