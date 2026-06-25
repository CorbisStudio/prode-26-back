from django.urls import path, re_path, include
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import (
    CustomTokenObtainPairView,
    HelloWorldView,
    ProfileView,
    RegisterView,
    ActivateView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Prode Back API",
        default_version='v1',
        description="API del proyecto Prode",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # ── Swagger / Redoc ────────────────────────────────────────────────────────
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # ── Auth: JWT (Bearer token) ───────────────────────────────────────────────
    # POST  /api/token/          → { username/email + password } → { access, refresh }
    # POST  /api/token/refresh/  → { refresh } → { access }
    # POST  /api/token/verify/   → { token }   → 200 / 401
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # ── Auto-registro con activación por código ─────────────────────────────────
    # POST /api/register/  → { first_name, email, password } → 201 (manda código por mail)
    # POST /api/activate/  → { email, code } → activa la cuenta → { access, refresh, user }
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/', ActivateView.as_view(), name='activate'),

    # ── Usuario autenticado ────────────────────────────────────────────────────
    # GET  /api/  → HOLA MUNDO
    # GET  /api/profile/  → datos del usuario logueado
    path('', HelloWorldView.as_view(), name='hello_world'),
    path('profile/', ProfileView.as_view(), name='profile'),

    # ── Mundial: partidos ───────────────────────────────────────────────────────
    path('', include('matches.urls')),

    # ── Prode: pronósticos, ranking y ligas ─────────────────────────────────────
    path('', include('predictions.urls')),
]
