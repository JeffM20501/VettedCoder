import factory

from tests.factories.base import TokenBearingFactory


class CandidateAccessTokenFactory(TokenBearingFactory):
    class Meta:
        model = "interviews.CandidateAccessToken"


class UserAuthTokenFactory(TokenBearingFactory):
    class Meta:
        model = "accounts.UserAuthToken"


class RefreshTokenFactory(TokenBearingFactory):
    class Meta:
        model = "accounts.RefreshToken"
