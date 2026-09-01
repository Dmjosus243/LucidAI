# -*- coding: utf-8 -*-
"""Tests des APIs bancaires & webhooks (Feature 7).

Vérifie l'idempotence (même événement -> même empreinte -> pas de doublon),
la stabilité des empreintes et les règles de génération.
"""
import pytest

from api.routes.banking import webhook_fingerprint


def test_fingerprint_with_event_id_is_deterministic():
    a = webhook_fingerprint("maishapay", "evt-123", {})
    b = webhook_fingerprint("maishapay", "evt-123", {})
    assert a == b
    assert a == "maishapay:evt-123"


def test_fingerprint_event_id_differs_between_events():
    assert webhook_fingerprint("maishapay", "evt-1", {}) != webhook_fingerprint("maishapay", "evt-2", {})


def test_fingerprint_content_hash_ignore_event_id_none():
    body = {"event_type": "transaction", "amount": 1500.5, "date": "2024-01-15"}
    a = webhook_fingerprint("generic", None, body)
    b = webhook_fingerprint("generic", None, body)
    assert a == b
    assert "generic:" not in a  # c'est un hash, pas un préfixe texte
    assert len(a) == 64  # sha256


def test_fingerprint_content_hash_sensitive_to_fields():
    body = {"event_type": "transaction", "amount": 1500.5, "date": "2024-01-15"}
    other = {"event_type": "transaction", "amount": 1500.5, "date": "2024-01-16"}
    assert webhook_fingerprint("generic", None, body) != webhook_fingerprint("generic", None, other)


def test_fingerprint_provider_scoped():
    body = {"event_type": "x", "amount": 1, "date": "2024-01-01"}
    assert webhook_fingerprint("proA", None, body) != webhook_fingerprint("proB", None, body)
    # et avec event_id, le provider est préfixé
    assert webhook_fingerprint("proA", "e", {}) == "proA:e"
    assert webhook_fingerprint("proB", "e", {}) == "proB:e"
