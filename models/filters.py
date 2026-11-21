"""Objetos de transferencia de datos entre vista, controlador y modelo."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FilterCriteria:
    """Criterios de filtrado. Una tupla vacía significa 'sin filtrar'."""

    categorias: tuple[str, ...] = ()
    tipos: tuple[str, ...] = ()
    municipios: tuple[str, ...] = ()
    titularidades: tuple[str, ...] = ()
    especialidades: tuple[str, ...] = ()
    texto: str = ""


@dataclass(frozen=True)
class Catalog:
    """Valores disponibles para poblar los filtros."""

    categorias: list[str] = field(default_factory=list)
    tipos_por_categoria: dict[str, list[str]] = field(default_factory=dict)
    municipios: list[str] = field(default_factory=list)
    titularidades: list[str] = field(default_factory=list)
    especialidades: list[str] = field(default_factory=list)
