from django.contrib import admin
from django.urls import path,include
from . import views
from .views import FineTunningListView

urlpatterns = [
    path('',FineTunningListView.as_view()),
    path('fine-tunning/',FineTunningListView.as_view(),name='models-list'),
    path('fine-tunning/create/',views.FineTuneExampleListView.as_view(),name='create-modal'),
    path('fine-tunning/create-job/',views.fine_tune,name='create-job'),
    path('fine-tunning/<str:job_id>/', views.FineTunnigDetailView.as_view(), name='fine-tune-model-detail'),
    path('select/<str:job_id>/', views.select_model, name='select-model'),
    path('playground/', views.PlayGroundView.as_view(), name='playground'),
    path('chat-logs/',views.ChatLogView.as_view(),name='chat-log'),
    path('users/',views.active_users_list,name='users-list'),
    path('users/<int:user_id>/conversations',views.user_conversations,name='conversations'),
    path('api-key/',views.ApiKey.as_view(),name='api-key'),
    # ########
    path('authorize/', views.authorize, name='authorize'),
    path('authorize/oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('clear/', views.clear_credentials, name='clear_credentials'),

]

