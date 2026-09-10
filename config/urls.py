from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

admin.site.site_header = 'EDEN GROUP — Administration'
admin.site.site_title = 'EDEN GROUP'
admin.site.index_title = 'Gestion de la plateforme foncière'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('eden.urls')),
    path('sw.js', TemplateView.as_view(
        template_name='sw.js',
        content_type='application/javascript'
    )),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)