"""Introspection instrumentation for runnable examples."""

import os
from contextlib import nullcontext
from functools import lru_cache

import logfire

try:
    from introspection_sdk import IntrospectionClient, IntrospectionSpanProcessor
except ImportError:  # pragma: no cover - introspection-sdk requires Python >=3.11
    IntrospectionClient = None
    IntrospectionSpanProcessor = None


SERVICE_NAME = 'bank-support-agent'


class NoOpIntrospection:
    def set_conversation(self, *_args, **_kwargs):
        return nullcontext()

    def set_agent(self, *_args, **_kwargs):
        return nullcontext()


@lru_cache(maxsize=1)
def configure_introspection():
    if IntrospectionClient is None or IntrospectionSpanProcessor is None:
        return NoOpIntrospection()

    client = IntrospectionClient(service_name=SERVICE_NAME)
    if os.getenv('INTROSPECTION_TOKEN'):
        logfire.configure(
            send_to_logfire='if-token-present',
            additional_span_processors=[
                IntrospectionSpanProcessor(service_name=SERVICE_NAME),
            ],
        )
        logfire.instrument_pydantic_ai()
    return client
