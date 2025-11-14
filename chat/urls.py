from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('chat/<uuid:session_id>/', views.chat_session, name='chat_session'),
    path('chat/<uuid:session_id>/send/', views.send_message, name='send_message'),
    path('chat/<uuid:session_id>/data/', views.view_data, name='view_data'),
    path('chat/<uuid:session_id>/delete/', views.delete_chat, name='delete_chat'),
    path('new-chat/', views.new_chat, name='new_chat'),
]
