# urls_api.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HerramientaViewSet, OrdenViewSet

router = DefaultRouter()
router.register(r'herramientas', HerramientaViewSet)
router.register(r'ordenes', OrdenViewSet)

urlpatterns = [
    path('', include(router.urls)),]