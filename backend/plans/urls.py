from django.urls import path
from .views import health, render_plan

urlpatterns = [
    path("health", health),
    path("render", render_plan),
]
