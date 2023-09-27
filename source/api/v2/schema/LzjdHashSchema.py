import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.LzjdHash import LzjdHash


class LzjdHashType(MongoengineObjectType):
    class Meta:
        model = LzjdHash


class LzjdHashQuery(graphene.ObjectType):
    lzjd_hash_list = graphene.List(LzjdHashType,
                                   object_id=graphene.List(graphene.String),
                                   name="lzjd_hash_list"
                                   )

    @superuser_required
    def resolve_lzjd_hash_list(self, info, object_id_list):
        return LzjdHash.objects(pk__in=object_id_list)
