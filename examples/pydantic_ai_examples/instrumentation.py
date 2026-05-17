from collections.abc import Iterator
from contextlib import contextmanager
from typing import Protocol

import logfire

try:
    from introspection_sdk import IntrospectionClient, IntrospectionSpanProcessor
except ImportError:
    IntrospectionClient = None
    IntrospectionSpanProcessor = None


class SupportsIntrospectionContext(Protocol):
    def set_agent(
        self, agent_name: str, agent_id: str | None = None
    ) -> Iterator[None]: ...

    def set_conversation(
        self,
        conversation_id: str | None = None,
        previous_response_id: str | None = None,
    ) -> Iterator[None]: ...

    def shutdown(self) -> None: ...


class NoOpIntrospection:
    @contextmanager
    def set_agent(self, agent_name: str, agent_id: str | None = None) -> Iterator[None]:
        yield

    @contextmanager
    def set_conversation(
        self,
        conversation_id: str | None = None,
        previous_response_id: str | None = None,
    ) -> Iterator[None]:
        yield

    def shutdown(self) -> None:
        pass


def configure_introspection() -> SupportsIntrospectionContext:
    if IntrospectionClient is None or IntrospectionSpanProcessor is None:
        logfire.configure(send_to_logfire='if-token-present')
        logfire.instrument_pydantic_ai()
        return NoOpIntrospection()

    logfire.configure(
        send_to_logfire='if-token-present',
        additional_span_processors=[
            IntrospectionSpanProcessor(service_name='bank-support')
        ],
    )
    logfire.instrument_pydantic_ai()
    return IntrospectionClient(service_name='bank-support')


def shutdown_introspection(introspection: SupportsIntrospectionContext) -> None:
    introspection.shutdown()
    logfire.shutdown()
