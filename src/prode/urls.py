from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

from api.views import HelloWorldView


def health(request):
    return JsonResponse({'status': 'ok', 'version': settings.APP_VERSION})


urlpatterns = [
    path('health', health),
    path('admin/', admin.site.urls),
    path('', HelloWorldView.as_view(), name='root_hello'),
    path('api/', include('api.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
