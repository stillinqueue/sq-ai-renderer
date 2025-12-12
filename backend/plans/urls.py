from django.urls import path
from .views import render_plan, health

urlpatterns = [
    path("health", health),
    path("render", render_plan),
]
