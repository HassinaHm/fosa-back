from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from fosa.views import FOSAViewSet, FOSAHistoryViewSet, GeoImportView
from fosa.views import WilayaViewSet, MoughataaViewSet, CommuneViewSet


from fosa.views import (
    FOSAViewSet, FOSAHistoryViewSet, GeoImportView,
    WilayaViewSet, MoughataaViewSet, CommuneViewSet,
    MaladieViewSet, MaladieReportViewSet
)

from fosa.views import (
    TypeStructureViewSet,
    NormePersonnelViewSet, NormeServiceViewSet, NormeMaterielViewSet,
    PersonnelStructureViewSet,
    ServiceStructureViewSet,
    MaterielStructureViewSet,FosaInitDefaultsViewSet
)
from accounts.views import AccessRequestViewSet

router = routers.DefaultRouter()
router.register("wilayas", WilayaViewSet, basename="wilaya")
router.register("moughataas", MoughataaViewSet, basename="moughataa")
router.register(r"communes", CommuneViewSet, basename="commune")
router.register(r"fosas", FOSAViewSet, basename="fosa")
router.register(r"history", FOSAHistoryViewSet, basename="history")

# ✅ Plan A: endpoints pour React
router.register(r"maladies", MaladieViewSet, basename="maladies")
router.register(r"maladie-reports", MaladieReportViewSet, basename="maladie-reports")

router.register("types-structures", TypeStructureViewSet, basename="types-structures")
router.register("normes-personnels", NormePersonnelViewSet, basename="normes-personnel")
router.register("normes-services", NormeServiceViewSet, basename="normes-services")
router.register("normes-materiels", NormeMaterielViewSet, basename="normes-materiel")

router.register(r"personnels", PersonnelStructureViewSet, basename="personnel")
router.register(r"services", ServiceStructureViewSet, basename="service")
router.register(r"materiels", MaterielStructureViewSet, basename="materiel")
router.register(r"fosa-init", FosaInitDefaultsViewSet, basename="fosa-init")
router.register(r"access-requests", AccessRequestViewSet, basename="access-requests")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/auth/", include("accounts.urls")),
    path("api/geo/import/", GeoImportView.as_view(), name="geo-import"),
    # path("api/structures-import/", StructureImportView.as_view(), name="structures-import"),

]