import os
import boto3
import fakeredis
import pytest
import respx
import time_machine
from moto import mock_aws

try:
    from rest_framework.test import APIClient
except ImportError:
    from django.test import Client as APIClient


@pytest.fixture
def clock():
    """Unified clock fixture wrapping time-machine per spec."""
    class ClockController:
        def __init__(self):
            self._traveller = None

        def set(self, target_time):
            if self._traveller:
                self._traveller.stop()
            self._traveller = time_machine.travel(target_time, tick=False)
            return self._traveller.start()

        def tick(self, duration=None):
            if self._traveller:
                if duration is not None:
                    self._traveller.shift(duration)
                else:
                    self._traveller.tick()

        def move_to(self, target_time):
            if self._traveller:
                self._traveller.move_to(target_time)
            else:
                self.set(target_time)

    controller = ClockController()
    yield controller
    if controller._traveller:
        controller._traveller.stop()


@pytest.fixture
def fake_redis():
    """Isolated fake Redis client for rate limits and presence tests."""
    server = fakeredis.FakeServer()
    client = fakeredis.FakeRedis(server=server, decode_responses=True)
    yield client
    client.flushall()


@pytest.fixture
def aws_mocks():
    """Moto mock covering S3 playback bucket and DynamoDB event tables."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="vettedcoder-playback-test")

        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="vc_session_events",
            KeySchema=[
                {"AttributeName": "session_id", "KeyType": "HASH"},
                {"AttributeName": "seq", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "session_id", "AttributeType": "S"},
                {"AttributeName": "seq", "AttributeType": "N"},
                {"AttributeName": "type_key", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "by_type",
                    "KeySchema": [
                        {"AttributeName": "session_id", "KeyType": "HASH"},
                        {"AttributeName": "type_key", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        dynamodb.create_table(
            TableName="vc_session_checkpoints",
            KeySchema=[
                {"AttributeName": "session_id", "KeyType": "HASH"},
                {"AttributeName": "elapsed_ms", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "session_id", "AttributeType": "S"},
                {"AttributeName": "elapsed_ms", "AttributeType": "N"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield {"s3": s3, "dynamodb": dynamodb}


@pytest.fixture
def mock_code_runner():
    """Respx mock router for sandbox execution service calls."""
    with respx.mock(base_url="http://localhost:8080", assert_all_called=False) as respx_mock:
        yield respx_mock


@pytest.fixture
def client():
    """Standard API client."""
    return APIClient()
