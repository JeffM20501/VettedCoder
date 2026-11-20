import factory

from tests.factories.base import BaseModelFactory


class InterviewSessionFactory(BaseModelFactory):
    class Meta:
        model = "interviews.InterviewSession"

    title = factory.Sequence(lambda n: f"Interview Session {n}")
    status = "scheduled"

    class Params:
        scheduled = factory.Trait(status="scheduled")
        in_progress = factory.Trait(status="in_progress")
        completed = factory.Trait(status="completed")
        cancelled = factory.Trait(status="cancelled")
        expired = factory.Trait(status="expired")


class SessionParticipantFactory(BaseModelFactory):
    class Meta:
        model = "interviews.SessionParticipant"

    role = "candidate"

    class Params:
        candidate = factory.Trait(role="candidate")
        interviewer = factory.Trait(role="interviewer")
        observer = factory.Trait(role="observer")
        host = factory.Trait(role="host")
