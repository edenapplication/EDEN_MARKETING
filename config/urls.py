from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = 'EDEN GROUP — Administration'
admin.site.site_title = 'EDEN GROUP'
admin.site.index_title = 'Gestion de la plateforme foncière'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('eden.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)