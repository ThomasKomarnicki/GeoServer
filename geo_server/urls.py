"""geo_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url, include
from rest_framework import routers
from django.contrib import admin
from geo.views import UserViewSet, LocationViewSet, LocationGuessViewSet, slideshow_info

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'locationGuess', LocationGuessViewSet)
router.register(r'locations', LocationViewSet)

google_auth_view = UserViewSet.as_view({'post':'google_auth'})

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^users/google_auth',google_auth_view, name='google_auth'),
    url(r'^slideshow_info',slideshow_info, name='slideshow_info'),
]

urlpatterns += router.urls