from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from PExpress.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pizza-express/', include('PExpress.urls')),
    path('', TemplateView.as_view(template_name='basis/first_page.html'), name='first'),
    path('api/', include('rest_framework.urls')),
    path('accounts/profile/', home),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)