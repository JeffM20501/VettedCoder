import factory

from tests.factories.base import BaseModelFactory, TokenBearingFactory


class OrganizationFactory(BaseModelFactory):
    class Meta:
        model = "organizations.Organizations"

    name = factory.Sequence(lambda n: f"Organization {n}")
    slug = factory.Sequence(lambda n: f"org-{n}")


class OrganizationInvitationFactory(TokenBearingFactory):
    class Meta:
        model = "organizations.OrganizationInvitation"

    email = factory.Sequence(lambda n: f"invited_{n}@example.com")
    role = "member"
