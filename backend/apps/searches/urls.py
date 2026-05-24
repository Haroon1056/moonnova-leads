from django.urls import path

from .views import (
    CreateSearchAPIView,
    SearchDetailAPIView,
    SearchListAPIView,
    PauseSearchAPIView,
    ResumeSearchAPIView,
    CancelSearchAPIView,
)

urlpatterns = [
    path("create/", CreateSearchAPIView.as_view()),
    path("list/", SearchListAPIView.as_view()),
    path("<int:search_id>/", SearchDetailAPIView.as_view()),

    # Search control
    path("<int:search_id>/pause/", PauseSearchAPIView.as_view()),
    path("<int:search_id>/resume/", ResumeSearchAPIView.as_view()),
    path("<int:search_id>/cancel/", CancelSearchAPIView.as_view()),
]