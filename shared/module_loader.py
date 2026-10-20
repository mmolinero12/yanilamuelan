"""Nombres estables para los directorios Python que contienen guiones."""
import importlib
import sys
from types import ModuleType
from shared.config import PROJECT_ROOT

PACKAGES = {"ingesta_rag": "ingesta-rag", "orquestacion_agentes": "orquestacion-agentes"}


def load_module(package: str, module: str):
    if package not in PACKAGES:
        raise ValueError("Paquete de integración desconocido.")
    if package not in sys.modules:
        namespace = ModuleType(package)
        namespace.__path__ = [str(PROJECT_ROOT / PACKAGES[package])]
        namespace.__package__ = package
        sys.modules[package] = namespace
    return importlib.import_module(f"{package}.{module}")
