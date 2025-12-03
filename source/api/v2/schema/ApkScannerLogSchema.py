import graphene
from graphql_jwt.decorators import superuser_required
from model.ApkScannerLog import ApkScannerLog
from api.v2.types.GenericFilter import generate_filter, get_filtered_queryset
from graphene_mongo import MongoengineObjectType
from graphene.relay import Node

ModelFilter = generate_filter(ApkScannerLog)

class ApkScannerLogType(MongoengineObjectType):
    class Meta:
        model = ApkScannerLog
        interfaces = (Node,)



class ApkScannerLogQuery(graphene.ObjectType):
    apk_scanner_log_list = graphene.List(ApkScannerLogType,
                                         object_id=graphene.List(graphene.String),
                                         field_filter=graphene.Argument(ModelFilter),
                                         name="apk_scanner_log_list"
                                         )

    @superuser_required
    def resolve_apk_scanner_log_list(self, info, object_id_list=None, field_filter=None):
        return get_filtered_queryset(ApkScannerLog, object_id_list, field_filter)
