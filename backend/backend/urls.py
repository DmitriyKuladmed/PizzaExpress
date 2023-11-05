from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pizza-express/', include('PExpress.urls')),
    path('', TemplateView.as_view(template_name='basis/first_page.html'), name='first'),
    path('api/', include('rest_framework.urls')),
]
