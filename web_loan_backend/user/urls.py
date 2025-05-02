from django.contrib import admin
from django.urls import path,include
from .views import hello_world,signup_view,index,login_view,password_reset_view,update_password_view,update_user_details,upload_csv_file,token_authorization_view,credit_score_calc_view

urlpatterns = [
    path('',index,name="index"),
    path('hello-world/', hello_world, name='hello-world'),
    path('register-user/', signup_view, name='signup'),
    path('login-user/', login_view, name='login'),
    path('reset-password/', password_reset_view, name='reset-password'),
    path('update-password/', update_password_view, name='update-password'),
    path('update-user-details/', update_user_details, name='update-user-details'),
    path('upload-csv/', upload_csv_file, name='upload-csv'),
    path('token-authorization/', token_authorization_view, name='token_authorization'),
    path('credit-evaluation/',credit_score_calc_view,name = 'credit_score_calculation'),
]