import graphene
import graphql_jwt
from api.v2.schema.UserAccountSchema import UserAccountQuery, UserAccountMutation
from api.v2.schema.RqJobsSchema import RqJobMutation
from graphene_django.debug import DjangoDebug


class Query(UserAccountQuery, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


class Mutation(UserAccountMutation, RqJobMutation, graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name='_debug')
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
