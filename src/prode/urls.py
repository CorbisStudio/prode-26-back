from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from api.views import HelloWorldView, HealthView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HelloWorldView.as_view(), name='root_hello'),
    path('health/', HealthView.as_view(), name='health'),
    path('api/', include('api.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
