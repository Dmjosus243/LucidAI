# -*- coding: utf-8 -*-
"""Tests de la piste d'audit et des rôles (Feature 6).

Les fonctions pures des rôles sont testées sans base de données.
Le contrôle d'accès par rôle est vérifié au niveau helper.
"""
import uuid

import pytest
from fastapi import HTTPException

from api.dependencies import (
    is_super_admin,
    is_org_admin,
    is_manager_or_above,
    require_org_admin,
    require_manager_or_above,
    require_super_admin,
)


def _user(role):
    class U:
        def __init__(self, role):
            self.id = str(uuid.uuid4())
            self.role = role
            self.is_active = True
    return U(role)


# ----------------------------------------------------------------------
# Prédicats de rôles
# ----------------------------------------------------------------------
@pytest.mark.parametrize("role,expect", [
    ("super_admin", True), ("org_admin", True), ("admin", True),
    ("manager", False), ("auditor", False),
])
def test_is_org_admin(role, expect):
    assert is_org_admin(_user(role)) is expect


@pytest.mark.parametrize("role,expect", [
    ("super_admin", True), ("org_admin", True), ("admin", True),
    ("manager", True), ("auditor", False),
])
def test_is_manager_or_above(role, expect):
    assert is_manager_or_above(_user(role)) is expect


def test_is_super_admin_only_for_super_admin():
    assert is_super_admin(_user("super_admin")) is True
    assert is_super_admin(_user("org_admin")) is False


# ----------------------------------------------------------------------
# Gardiens (lèvent HTTPException 403 si le rôle est insuffisant)
# ----------------------------------------------------------------------
def test_require_org_admin_ok_for_admin():
    require_org_admin(_user("admin"))  # ne doit pas lever


def test_require_org_admin_rejects_auditor():
    with pytest.raises(HTTPException) as exc:
        require_org_admin(_user("auditor"))
    assert exc.value.status_code == 403


def test_require_manager_or_above_rejects_auditor():
    with pytest.raises(HTTPException) as exc:
        require_manager_or_above(_user("auditor"))
    assert exc.value.status_code == 403


def test_require_manager_or_above_ok_for_manager():
    require_manager_or_above(_user("manager"))  # ne doit pas lever


def test_require_super_admin_rejects_org_admin():
    with pytest.raises(HTTPException):
        require_super_admin(_user("org_admin"))
