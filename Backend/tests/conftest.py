# -*- coding: utf-8 -*-
"""Configuration pytest partagée pour les tests backend LucidAI.

Les tests du moteur sont unitaires et ne requièrent aucune base de données.
Les tests d'intégration exigeant une DB sont marqués @pytest.mark.integration et
sont ignorés par défaut (lancer pytest -m integration explicitement).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: tests requiring a live database / external services"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("-m"):
        skip_integration = pytest.mark.skip(
            reason="test d'intégration : nécessite une base/externe. "
                   "Ajouter -m integration pour l'exécuter."
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
