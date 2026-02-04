from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views_auth import RegisterView

from rest_framework.routers import DefaultRouter
from .views import GeoImportView, WilayaViewSet, MoughataaViewSet, CommuneViewSet

from .views import (
    TypeStructureViewSet,
    NormePersonnelViewSet, NormeServiceViewSet, NormeMaterielViewSet,
    StructureSanteViewSet
)
router = DefaultRouter()

router.register(r"wilayas", WilayaViewSet, basename="wilaya")
router.register(r"moughataas", MoughataaViewSet, basename="moughataa")
router.register(r"communes", CommuneViewSet, basename="commune")

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]


