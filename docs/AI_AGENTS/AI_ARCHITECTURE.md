# AI Shopping Copilot - AI Architecture

Version: 1.0
Status: Design Phase
Author: Surya
Architecture Style: Modular AI Platform
Last Updated: July 2026

---

# Vision

AI Shopping Copilot is not a chatbot.

It is an intelligent shopping decision platform that helps users discover, compare, evaluate, and plan purchases using AI reasoning and structured product data.

The system is designed to be:

- Modular
- Secure
- Scalable
- Observable
- Cost Efficient
- Easy to extend

The AI never directly accesses databases or external systems.

Everything happens through controlled tools.

---

# Goals

The AI should help users:

✓ Search products

✓ Compare products

✓ Recommend products

✓ Explain trade-offs

✓ Find better alternatives

✓ Analyze reviews

✓ Track price history

✓ Build shopping plans

✓ Make better buying decisions

---

# Non Goals

The AI should NOT:

❌ Answer general knowledge questions

❌ Write code

❌ Explain history

❌ Predict stock markets

❌ Give legal advice

❌ Give medical advice

❌ Access unsupported websites

❌ Invent products

❌ Invent prices

❌ Generate fake reviews

---

# Target Users

Phase 1

Single User

The project owner uses the AI to make shopping decisions.

---

Future

Multiple users

Families

Small businesses

Enterprise shopping teams

---

# Supported Product Categories

Phase 1

Laptop

Mobile Phone

---

Future

Tablet

Monitor

Keyboard

Mouse

GPU

CPU

Headphones

Smart Watch

Camera

Home Appliances

---

# User Journey

User opens application

↓

Types a question

↓

Gateway receives request

↓

Security checks request

↓

Intent Classification

↓

Model Selection

↓

Planner

↓

Tool Execution

↓

LLM Reasoning

↓

Response Validation

↓

User receives answer

---

# Request Lifecycle

User Request

↓

Authentication

↓

Request Middleware

↓

Rate Limiting

↓

Guardrails

↓

Prompt Injection Detection

↓

Intent Classifier

↓

Model Router

↓

Planner

↓

Tool Executor

↓

Database

↓

LLM

↓

Response Validator

↓

Monitoring

↓

Final Response

---

# AI Layers

Layer 1

Gateway

Responsibilities

Receive requests

Generate Request ID

Logging

Authentication

API Validation

Future

API Keys

OAuth

JWT

---

Layer 2

Security Layer

Responsibilities

Prompt Injection Detection

Jailbreak Detection

SQL Injection Detection

Spam Detection

Input Validation

Unsupported Request Detection

Output

Allowed

Blocked

Need Clarification

---

Layer 3

Intent Classification

Purpose

Understand what user wants.

Supported Intents

SEARCH_PRODUCT

COMPARE_PRODUCTS

RECOMMEND_PRODUCT

PRICE_HISTORY

PRICE_DROP

PRODUCT_DETAILS

REVIEW_SUMMARY

SHOPPING_PLAN

GENERAL_CHAT

UNSUPPORTED

---

Layer 4

Guardrails

Purpose

Restrict AI to shopping domain.

Example

User

Show me headphones

System

Currently only laptops and mobile phones are supported.

The LLM should never hallucinate unsupported products.

---

Layer 5

Model Router

Purpose

Choose the best model.

Simple Search

↓

Small Model

Comparison

↓

Medium Model

Planning

↓

Large Model

Future Providers

Ollama

Gemma

Qwen

Llama

GPT

Claude

Gemini

---

Layer 6

Planner

Purpose

Break complex requests into steps.

Example

Compare iPhone and Samsung.

Plan

Search Product

↓

Fetch Reviews

↓

Fetch Prices

↓

Compare

↓

Summarize

---

Layer 7

Tool Layer

The AI never accesses PostgreSQL directly.

It only uses tools.

Examples

search_products()

compare_products()

get_price_history()

get_reviews()

recommend_products()

find_cheapest()

find_best_rated()

wishlist()

Each tool is independently testable.

---

Layer 8

Memory

Phase 1

Conversation Memory

Future

User Preferences

Favorite Brands

Shopping History

Budget

Wishlist

Purchase History

---

Layer 9

Reasoning Layer

Receives

User Question

Tool Outputs

Conversation Context

Produces

Natural language response.

---

Layer 10

Response Validation

Verify

No hallucinations

No unsupported products

No prompt leakage

No internal errors

Safe response

---

Layer 11

Monitoring

Track

Request ID

Execution Time

Latency

Model Used

Tokens

Tools Used

Errors

Success Rate

Future

Grafana Dashboard

---

Layer 12

Evaluation

Automatically test

Accuracy

Latency

Tool Success

Hallucination Rate

Cost

Prompt Quality

---

# Tool Architecture

Every capability is implemented as a tool.

Product Tools

search_products()

get_product_details()

compare_products()

Recommendation Tools

recommend_products()

find_best_value()

Review Tools

review_summary()

sentiment_analysis()

Price Tools

price_history()

price_drop()

Wishlist Tools

create_wishlist()

add_to_wishlist()

remove_from_wishlist()

Future Tools

Notification Tool

Budget Planner

Shopping Planner

---

# AI Decision Flow

Simple Question

↓

Intent

↓

Tool

↓

Database

↓

LLM

↓

Answer

Complex Question

↓

Intent

↓

Planner

↓

Multiple Tools

↓

LLM

↓

Answer

---

# Database Access

The AI never queries SQL.

Instead

PostgreSQL

↓

Repository

↓

Python Objects

↓

Structured JSON

↓

LLM

↓

Response

---

# Observability

Every request produces

Request Trace

Tool Trace

Model Trace

Execution Time

Token Usage

Error Logs

---

# Cost Optimization

Simple requests

↓

Small local model

Complex reasoning

↓

Large model

The objective is to minimize cost while maintaining quality.

---

# Future Multi-Agent Architecture

Coordinator Agent

↓

Search Agent

↓

Price Agent

↓

Review Agent

↓

Recommendation Agent

↓

Planner Agent

Initially only one orchestrator agent will be implemented.

The architecture allows future migration to multi-agent systems without major refactoring.

---

# Guiding Principles

The LLM is not the system.

The LLM is one component inside the system.

Security first.

Tools before prompting.

Structured data before reasoning.

Measure everything.

Never trust AI without validation.

Keep every layer independently replaceable.

---

# Phase Roadmap

Phase 8.1

Gateway

Phase 8.2

Security

Phase 8.3

Intent Classification

Phase 8.4

Guardrails

Phase 8.5

Model Router

Phase 8.6

Planner

Phase 8.7

Tool Layer

Phase 8.8

Reasoning Layer

Phase 8.9

Response Validation

Phase 8.10

Monitoring

Phase 8.11

Evaluation

Phase 8.12

Multi-Agent Upgrade

---

# Long-Term Vision

Build an AI Platform, not just an AI Agent.

The same platform should support future domains by replacing only:

- Tools
- Prompts
- Product categories

without changing the core architecture.

The AI platform should remain modular, observable, secure, scalable, and production-ready.