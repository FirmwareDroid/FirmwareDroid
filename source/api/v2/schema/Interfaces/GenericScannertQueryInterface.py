import graphene
from graphene import Interface
from graphene_django.debug import DjangoDebug
from graphql_jwt.decorators import superuser_required


class GenericDocumentQueryInterface(Interface):
    debug = graphene.Field(DjangoDebug, name='_debug')

    class Meta:
        description = "Basic document resolver fields"

    @superuser_required
    def resolve_document_list(self, info, object_id_list):
        raise NotImplementedError

