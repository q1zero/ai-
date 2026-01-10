from __future__ import annotations

from django.urls import path

from .views import (
    GenerateScriptView,
    PreviewScriptView,
    StartRenderView,
    VideoProjectListView,
    VideoProjectView,
    VideoScriptView,
)

urlpatterns = [
    path("preview_script/", PreviewScriptView.as_view(), name="preview-script"),
    path("generate_script/", GenerateScriptView.as_view(), name="generate-script"),
    path("start_render/", StartRenderView.as_view(), name="start-render"),
    path("projects/", VideoProjectListView.as_view(), name="video-project-list"),
    path("projects/<int:project_id>/", VideoProjectView.as_view(), name="video-project"),
    path("scripts/<int:script_id>/", VideoScriptView.as_view(), name="video-script"),
]
