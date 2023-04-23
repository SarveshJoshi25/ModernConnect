from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('modern_connect/admin/', admin.site.urls),
    path('modern_connect/api/v1/', include('modernConnect.urls'))
]
