from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter
from records import views

router = DefaultRouter()
router.register(r'records', views.TestRecordListViewSet, base_name="records")
router.register(r'branches', views.TestBranchListViewSet, base_name="branches")
router.register(r'records-by-branch', views.TestRecordListByBranchViewSet, base_name="records-by-branch")
router.register(r'detail', views.TestRecordDetailViewSet, base_name="detail")

urlpatterns = [
	url(r'^', include(router.urls))
]