from django.urls import path
from . import views
urlpatterns = [
    # path('', views.sign_in, name='signin'),
    path('', views.dashboard, name='signin'),
    path('home/' , views.homePage , name = 'home'),
    path('signup/', views.sign_up, name='signup'),
    path('api/tasks/', views.get_task, name='get_tasks'),
    path('api/tasks/<int:task_id>/', views.delete_task, name='delete_task'),
    path('api/tasks/<int:task_id>/complete/', views.mark_completed, name='complete_task'),
    path('contact/success', views.contact_success_view, name='contact-success'),
    path('api/ttn/temperature/', views.get_ttn_temperature, name='ttn_temperature'),
    path('api/ttn/payload/send/', views.send_manual_ttn_payload, name='send_manual_payload'),
    path('api/ttn/test/', views.test_ttn_config, name='ttn_test'),
]