"""Unit tests verifying AI Gateway components, pipelines, and middlewares."""

import pytest

from src.ai_agents.exceptions import LLMException
from src.ai_agents.gateway.context_builder import AIContextBuilder
from src.ai_agents.gateway.gateway import AIGateway
from src.ai_agents.gateway.middleware import AIGatewayMiddleware
from src.ai_agents.gateway.pipeline import AIGatewayPipeline
from src.ai_agents.gateway.request_handler import AIRequestHandler
from src.ai_agents.gateway.response_handler import AIResponseHandler, GatewayResponse
from src.ai_agents.schemas.request import AIRequest
from src.ai_agents.schemas.response import AIResponse


@pytest.fixture
def request_handler() -> AIRequestHandler:
    return AIRequestHandler()


@pytest.fixture
def context_builder() -> AIContextBuilder:
    return AIContextBuilder()


@pytest.fixture
def middleware() -> AIGatewayMiddleware:
    return AIGatewayMiddleware()


@pytest.fixture
def response_handler() -> AIResponseHandler:
    return AIResponseHandler()


@pytest.fixture
def pipeline(
    request_handler: AIRequestHandler,
    context_builder: AIContextBuilder,
    middleware: AIGatewayMiddleware,
    response_handler: AIResponseHandler,
) -> AIGatewayPipeline:
    return AIGatewayPipeline(
        request_handler=request_handler,
        context_builder=context_builder,
        middleware=middleware,
        response_handler=response_handler,
    )


@pytest.fixture
def gateway(pipeline: AIGatewayPipeline) -> AIGateway:
    return AIGateway(pipeline=pipeline)


def test_request_handler_validation(request_handler: AIRequestHandler) -> None:
    """Verify that request_handler creates a validated AIRequest and checks values."""
    req = request_handler.handle(prompt="Hello laptop", conversation_id="conv_123", request_id="req_123")
    assert req.prompt == "Hello laptop"
    assert req.conversation_id == "conv_123"
    assert req.request_id == "req_123"


def test_request_handler_missing_ids(request_handler: AIRequestHandler) -> None:
    """Verify that request_handler generates unique correlation IDs when omitted."""
    req1 = request_handler.handle(prompt="Laptops under $1000")
    req2 = request_handler.handle(prompt="Mobiles under $500")

    assert req1.request_id.startswith("req_")
    assert req1.conversation_id.startswith("conv_")
    assert req2.request_id.startswith("req_")
    assert req2.conversation_id.startswith("conv_")
    assert req1.request_id != req2.request_id
    assert req1.conversation_id != req2.conversation_id


def test_context_builder_trace_generation(request_handler: AIRequestHandler, context_builder: AIContextBuilder) -> None:
    """Verify context builder handles trace ID normalization."""
    req = request_handler.handle(prompt="Specs for phone")
    context = context_builder.build(request=req, trace_id="custom_trace_id_456")
    
    assert context.tracing_metadata is not None
    assert context.tracing_metadata.trace_id == "custom_trace_id_456"


@pytest.mark.asyncio
async def test_gateway_success_pipeline(gateway: AIGateway) -> None:
    """Verify that a successful gateway run outputs formatted GatewayResponse."""
    res: GatewayResponse = await gateway.process_request(
        prompt="Compare Apple and Dell",
        conversation_id="conv_custom_id",
    )

    assert res.success is True
    assert res.latency_ms > 0.0
    assert res.response is not None
    assert res.response.conversation_id == "conv_custom_id"
    assert "latency_ms" in res.response.metadata
    assert res.response.metadata["trace_id"] is not None


@pytest.mark.asyncio
async def test_gateway_exception_handling(gateway: AIGateway) -> None:
    """Verify that exceptions raised in the lifecycle are serialized correctly into error envelopes."""
    async def failing_next(req: AIRequest, trace: str) -> AIResponse:
        raise LLMException(
            message="LLM provider connection lost.",
            error_code="LLM_CONNECTION_FAILED",
            details={"provider": "gemini"},
        )

    res: GatewayResponse = await gateway.process_request(
        prompt="Find phone",
        next_call=failing_next,
    )

    assert res.success is False
    assert res.error_code == "LLM_CONNECTION_FAILED"
    assert res.error_message is not None
    assert "connection lost" in res.error_message
    assert res.error_details == {"provider": "gemini"}
    assert res.latency_ms > 0.0
