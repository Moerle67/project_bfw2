from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('', views.start, name= 'start'),
    path('g_pdf/<int:id>/<int:typ>', views.gen_pdf, name= 'gen_pdf'),
    path('design/<int:id>', views.klaus_design, name= 'klausur_design'),
    path('pos/<int:klausur>/<int:frage>/<int:richtung>', views.richtung, name= 'richtung'),
    path('random/<int:klausur>', views.zufall, name= 'zufall'),
    path('newside/<int:klausur>', views.newside, name= 'newside'),
    path('evaluation/<int:klausur>', views.evaluation, name= 'evaluation'),
    path('evaluation2/<int:klausur>/<int:tn>', views.evaluation2, name= 'evaluation2'),
]