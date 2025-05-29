from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('initiate/<int:ad_id>/', views.initiate_payment, name='initiate_payment'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
]