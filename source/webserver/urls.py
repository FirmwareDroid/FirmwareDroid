from django.urls import path, include
from graphene_django.views import GraphQLView
from django.contrib import admin
from graphql_jwt.decorators import jwt_cookie

urlpatterns = [
    path('', include('setup.urls')),
    path("admin/", admin.site.urls),
    path("graphql/", jwt_cookie(GraphQLView.as_view(graphiql=True))),
    path("django-rq/", include('django_rq.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path("", include("file_download.urls")),
]
