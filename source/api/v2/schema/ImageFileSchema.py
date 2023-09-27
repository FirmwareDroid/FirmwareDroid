import graphene
from graphene_mongo import MongoengineObjectType
from graphql_jwt.decorators import superuser_required
from model.ImageFile import ImageFile


class ImageFileType(MongoengineObjectType):
    class Meta:
        model = ImageFile


class ImageFileQuery(graphene.ObjectType):
    image_file_list = graphene.List(ImageFileType,
                                    object_id_list=graphene.List(graphene.String),
                                    name="image_file_list")

    @superuser_required
    def resolve_image_file_list(self, info, object_id_list):
        return ImageFile.objects(pk__in=object_id_list)
