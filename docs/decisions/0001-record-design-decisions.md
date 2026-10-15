# 0001. Record design decisions

- Status: accepted. Proposed by the assistant.
- Date: 2026-10-15

## Context

Visualific is opinionated: it fixes type sizes, widths, colours and layout rules on behalf of its users. Those choices need to be explained and open to challenge. The project is also developed with an AI coding assistant. JOSS, for example, asks authors to affirm that people made the primary architectural and design decisions.

## Decision

Each significant design decision gets a short record in this folder, numbered in order. A record states the context, the decision and its consequences, and says who made the decision when the assistant made it. A decision that changes later gets a new record that supersedes the old one; old records are kept.

## Consequences

- Users can see why a default exists before asking to change it.
- Reviewers can trace the design history.
- Small choices that follow from an existing record do not need a record of their own.
