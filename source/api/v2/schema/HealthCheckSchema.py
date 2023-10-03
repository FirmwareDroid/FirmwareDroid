import graphene


class HealthCheckQuery(graphene.ObjectType):
    is_api_up = graphene.Boolean()

    def resolve_is_api_up(self, info):
        return True
