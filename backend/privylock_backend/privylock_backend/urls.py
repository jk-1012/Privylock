"""
URL configuration for privylock_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
PrivyLock URL Configuration

Main URL routing for the entire Django project.
Routes requests to appropriate apps (users, vault, notifications).

URL Structure:
- /admin/ - Django admin panel
- /api/auth/ - Authentication endpoints (users app)
- /api/vault/ - Document vault endpoints (vault app)
- /api/notifications/ - Notification endpoints (notifications app)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin Panel
    path('admin/', admin.site.urls),

    # API Endpoints
    path('api/auth/', include('users.urls')),
    path('api/vault/', include('vault.urls')),
#path('api/notifications/', include('notifications.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

# Custom admin site headers
admin.site.site_header = "PrivyLock Administration"
admin.site.site_title = "PrivyLock Admin"
admin.site.index_title = "Welcome to PrivyLock Administration"
