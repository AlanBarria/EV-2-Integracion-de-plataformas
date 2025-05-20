from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView
from ferremas.views import confirmar_pago, logout_view
from django.contrib.auth.views import LogoutView
from ferremas.views import convert_currency
from ferremas.views import update_cart_total

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('ferremas.urls')),
    path('webpay/confirmar/', confirmar_pago, name='webpay_confirmar'),
    path('', RedirectView.as_view(url='/api/', permanent=False)),
    path('api/', include('ferremas.urls_api')),  
    path('api/logout/', logout_view, name='logout'),
    path('api/convert/', convert_currency,),
    path('api/update_cart_total/' ,update_cart_total),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
