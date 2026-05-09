"""Routing prompts — system instructions for LLM-assisted routing (future use).

Currently the router is keyword-based (no LLM). This module defines the prompts
that would be used if the router is upgraded to an LLM-assisted approach.
"""
from __future__ import annotations

ROUTER_SYSTEM_PROMPT = """You are a document analysis router.
Given a user request, classify it into exactly one of these analysis types:
  - summary     : general summarisation or overview request
  - financial   : anything involving numbers, revenue, profit, ratios, growth
  - comparison  : comparing two or more documents or datasets
  - legal       : contract review, legal clauses, compliance
  - audit       : internal audit, controls, risk, findings
  - custom      : any request that doesn't fit the above categories

Respond with a single word — the analysis type name. No explanation."""

ROUTER_USER_TEMPLATE = "User request: {prompt}"
