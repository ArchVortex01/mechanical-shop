from pathlib import Path
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve
from django.shortcuts import redirect

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR.parent / 'frontend'

def root_redirect(request):
    return redirect('/html/index.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', root_redirect, name='root-redirect'),
    re_path(r'^(?P<path>.*)$', serve, {'document_root': FRONTEND_DIR}),
]
