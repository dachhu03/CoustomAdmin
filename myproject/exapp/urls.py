from django.urls import path, include
from .views import *
from django.contrib.auth.views import LogoutView

urlpatterns = [
 path("", home, name="home"),
#  path("signup/", authView, name="authView"),
path('login/', login_view, name='login'),
 path('logout/', LogoutView.as_view(next_page='exapp:login'), name='logout'),
 path("totalsolutions/",totalsolutions, name="totalsolutions"),
 path("additem/",additem, name="additem"),
 path("delete/<str:id>",delete, name="delete"),
 path('edit/<int:id>/', edit, name='edit'),
 path("accounts/", include("django.contrib.auth.urls")),
 path('upload/', upload_file, name='upload'),
 path('update_field/',update_field, name='update_field'),
 path('boq/', boq , name='boq'),
 path('generate-token' , generate_token, name='generate_token'),
 path('view-with-token' , view_with_token , name= 'view_with_token'),
 path('validate-token' , validate_token , name='validate_token'),

 
]

