# 0012 — Integrations support full functionality; no SoapySDR module

- Status: accepted (ON8ST, 2026-11-19)
- Date: 2026-11-19

## Context

A host-side SoapySDR module for level 1 (0011) was proposed as a generic route to SDR
software that does not know G7250-P1. SoapySDR carries IQ only, and generic SoapySDR
applications do not know about PTT or ATU logic, so the module would at first have been
RX-only (discussion, 2026-11-19).

## Decision

1. Every integration we deliver supports the full functionality of the radio, including
   transmit (ON8ST, 2026-11-19).
2. A SoapySDR module is not pursued, because it would not meet point 1.

## Consequences

- Alternatives for easy integration on level 1 are evaluated against point 1.
- RX-only deliverables may exist as intermediate milestones, but not as a final product.
- Transmit through any integration remains bounded by the safety core in the radio (0011).

## Sources

- Discussion with ON8ST, 2026-11-19.
