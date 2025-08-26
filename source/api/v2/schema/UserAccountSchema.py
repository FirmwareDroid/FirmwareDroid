# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import graphene
from graphql_jwt.decorators import superuser_required
from setup.models import User
from graphene_django import DjangoObjectType
from api.v2.validators.validation import (
    sanitize_and_validate, sanitize_email, sanitize_username,
    validate_email, validate_username, validate_password
)


class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude = ("password",)


class UserAccountQuery(graphene.ObjectType):
    users = graphene.List(UserType)
    me = graphene.Field(UserType)

    @superuser_required
    def resolve_users(self, info):
        user = info.context.user
        if user.is_anonymous and user.is_authenticated:
            raise ValueError('Not logged in!')
        return User.objects.all()

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous and user.is_authenticated:
            raise ValueError(f'Not logged in! {user}')
        return user


class CreateUser(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        is_superuser = graphene.Boolean(required=False)

    @classmethod
    @superuser_required
    @sanitize_and_validate(
        validators={
            'username': validate_username,
            'password': validate_password,
            'email': validate_email
        },
        sanitizers={
            'username': sanitize_username,
            'email': sanitize_email
        }
    )
    def mutate(cls, root, info, username, password, email, is_superuser):
        user = User(
            username=username,
            email=email,
            password=password,
            is_superuser=is_superuser
        )
        user.save()
        return cls(ok=True)


class DeleteUser(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        username = graphene.String(required=True)

    @classmethod
    @sanitize_and_validate(
        validators={'username': validate_username},
        sanitizers={'username': sanitize_username}
    )
    def mutate(cls, root, info, username):
        obj = User.objects.get(username=username)
        obj.delete()
        return cls(ok=True)


class UserAccountMutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    delete_user = DeleteUser.Field()
