from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from users.views import LoginWithOTPView, VerifyOTPView, GoogleLoginView
from django.conf import settings
from django.conf.urls.static import static
from agent_api import views as agent_api_views


def ping(request):
    """Lightweight no-DB endpoint for keep-alive pings."""
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('ping/', ping, name='ping'),
    path('', RedirectView.as_view(url='/api/products/')),
    path('admin/', admin.site.urls),
    path('.well-known/agent-commerce.json', agent_api_views.agent_manifest, name='agent_manifest'),
    path('api/auth/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/sellers/', include('sellers.urls')),
    path('api/agent/v1/', include('agent_api.urls')),
    path('api/ai/chat/', __import__('intelligence.views', fromlist=['AgenticChatView']).AgenticChatView.as_view(), name='agentic_chat'),
    path('api/intelligence/', include('intelligence.urls')),
    path('api/agent-runtime/', include('agent_runtime.urls')),
    path('api/', include('orders.urls')),
    path('api/crm/', include('crm.urls')),
    path('api/wishlist/', include('wishlist.urls')),
    path('api/token/', LoginWithOTPView.as_view(), name='token_obtain_pair'),
    path('api/auth/google/', GoogleLoginView.as_view(), name='google_login'),
    path('api/token/verify-2fa/', VerifyOTPView.as_view(), name='token_verify_2fa'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
