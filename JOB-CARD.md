# Job Card: LLM Support Triage

## Problem

Support messages arrive as unstructured text and require a person to classify the issue, assess urgency, and choose the responsible team.

## User

A support operator or system that needs a consistent first-pass routing decision.

## Input and output

- Input: one `text` string containing 1–2000 characters.
- Output: validated JSON containing a closed category, urgency, suggested team, confidence score, and one-sentence reason.

## Provider

- API: OpenRouter's OpenAI-compatible endpoint.
- Model: `google/gemma-4-26b-a4b-it:free`.
- Data rule: use only synthetic or non-confidential support text with the free provider.

## Success

`POST /triage` returns only schema-valid routing JSON, safely handles invalid model output and provider failures, and can be configured and tested from a fresh clone in under five minutes.

## Not in scope

Chat, memory, persistence of triage results, UI, streaming, agents, RAG, queues, and automated high-impact decisions.
