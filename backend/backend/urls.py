from django.urls import path, include

urlpatterns = [
    path("api/plans/", include("plans.urls")),
]
