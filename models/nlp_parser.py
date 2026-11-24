"""Parser ligero de búsquedas en lenguaje natural para el catálogo sanitario."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from models.filters import Catalog, FilterCriteria


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFD", value.lower())
    return "".join(char for char in text if unicodedata.category(char) != "Mn")


def _contains_phrase(query: str, value: str) -> bool:
    """Match a normalized catalog phrase on word boundaries."""
    phrase = normalize(value).strip()
    return bool(phrase and re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", query))


def parse_search(text: str, catalog: Catalog) -> FilterCriteria:
    """Extrae filtros conocidos con coincidencias normalizadas y tolerantes."""
    query = normalize(text)

    categorias = tuple(value for value in catalog.categorias if _contains_phrase(query, value))
    tipos = tuple(
        value for value in catalog.tipos_por_categoria.values()
        for value in value
        if _contains_phrase(query, value)
    )
    municipios = tuple(
        value for value in catalog.municipios
        if value != "Sin dato" and _contains_phrase(query, value)
    )

    service_aliases = {
        "urgencias y emergencias": ("urgencias", "emergencia", "emergencias", "accidente", "sos"),
        "pediatria": ("pediatria", "pediatra", "pediatricos", "pediatrico", "ninos", "nino", "ninas", "infantil", "bebe", "bebes", "adolescente", "adolescentes"),
        "odontologia/estomatologia": ("odontologia", "estomatologia", "dentista", "dentistas", "dental", "dientes", "boca"),
        "cardiologia": ("cardiologia", "cardiologo", "cardiaca", "cardiaco", "corazon"),
        "psiquiatria infantil y de la adolescencia": ("psiquiatria infantil", "psicologo infantil", "salud mental infantil", "adolescente", "ninos"),
        "laboratorio clinico": ("laboratorio", "analisis", "analitica", "sangre", "prueba analitica"),
    }

    query_tokens = re.findall(r"[a-z0-9]+", query)

    def service_matches(service: str) -> bool:
        if not query.strip():
            return False

        normalized_service = normalize(service)
        if _contains_phrase(query, normalized_service):
            return True

        aliases = service_aliases.get(normalized_service, ())
        if any(_contains_phrase(query, alias) for alias in aliases):
            return True

        alias_words = {
            word
            for alias in aliases
            for word in re.findall(r"[a-z0-9]+", alias)
        }
        for candidate in query_tokens:
            if len(candidate) >= 4:
                for target in alias_words:
                    if SequenceMatcher(None, candidate, target).ratio() >= 0.82:
                        return True
        return False

    especialidades = tuple(
        value for value in catalog.especialidades
        if service_matches(value)
    )

    titularidades = []
    if re.search(r"\b(public[oa]s?|salud publica|administracion)\b", query):
        titularidades.append("Público")
    if re.search(r"\b(privad[oa]s?|clinica privada)\b", query):
        titularidades.append("Privado")

    radius_match = re.search(r"(?:radio(?: de)?|a menos de|en un radio de)\s*(\d+)\s*(?:km|kilometros?|metros?)?", query)
    radius_km = 10.0
    if radius_match:
        amount = float(radius_match.group(1))
        unit = query[radius_match.start():radius_match.end()]
        radius_km = amount / 1000 if "metro" in unit and "kilometro" not in unit else amount

    location = _extract_location(text)
    if not location and municipios:
        location = municipios[0]

    recognized_terms = {
        word
        for value in (*categorias, *tipos, *municipios, *titularidades)
        for word in re.findall(r"[a-z0-9]+", normalize(value))
    }
    if "Público" in titularidades:
        recognized_terms.update(("publico", "publica", "administracion"))
    if "Privado" in titularidades:
        recognized_terms.update(("privado", "privada", "clinica"))
    for service in especialidades:
        normalized_service = normalize(service)
        aliases = service_aliases.get(normalized_service, ())
        recognized_terms.update(
            word
            for term in (normalized_service, *aliases)
            for word in re.findall(r"[a-z0-9]+", term)
        )

    if location:
        recognized_terms.update(re.findall(r"[a-z0-9]+", normalize(location)))

    # Strip recognized catalog phrases before free-text extraction. Exact
    # filters still carry these constraints; residual text is only for terms
    # the catalog does not understand.
    radius_text = re.sub(
        r"(?:radio(?:\s+de)?|a\s+menos\s+de|en\s+un\s+radio\s+de)\s*\d+\s*(?:km|kilometros?|metros?)?",
        " ",
        query,
    )
    for value in (*categorias, *tipos, *municipios):
        radius_text = re.sub(
            rf"(?<![a-z0-9]){re.escape(normalize(value))}(?![a-z0-9])",
            " ",
            radius_text,
        )
    stop_words = {
        "a", "al", "busco", "buscar", "con", "de", "del", "el", "en", "la",
        "cerca", "desde", "kilometro", "kilometros", "km", "las", "los", "me",
        "menos", "necesito", "para", "por", "radio", "metro", "metros", "quiero",
        "un", "una",
    }
    texto = " ".join(
        word
        for word in re.findall(r"[a-z0-9]+", radius_text)
        if word not in recognized_terms and word not in stop_words
    )

    reason = ""
    reason_candidates = []
    for service in especialidades:
        normalized_service = normalize(service)
        aliases = service_aliases.get(normalized_service, ())
        terms = tuple(dict.fromkeys((normalized_service, *aliases)))
        positions = [position for term in terms if (position := query.find(term)) >= 0]
        if positions:
            reason_candidates.append((min(positions), service))
    if reason_candidates:
        reason = min(reason_candidates, key=lambda item: item[0])[1]

    return FilterCriteria(
        categorias=tuple(dict.fromkeys(categorias)),
        tipos=tuple(dict.fromkeys(tipos)),
        municipios=tuple(dict.fromkeys(municipios)),
        titularidades=tuple(dict.fromkeys(titularidades)),
        especialidades=tuple(dict.fromkeys(especialidades)),
        texto=texto,
        location=location,
        reason=reason,
        radius_km=radius_km,
    )


def _extract_location(text: str) -> str:
    patterns = (
        r"(?:cerca de|desde|ubicado en|direcci[oó]n)\s+(.+?)(?:\s*(?:radio|a menos de|publico|publica|privado|privada|urgencias|cardiolog|pediatr)|$)",
        r"\ben\s+(?!(?:el|la|los|las|un|una)\b)([A-ZÁÉÍÓÚÑ][^,]*?)(?=\s+(?:con\s+)?(?:un\s+)?radio\b|\s+(?:public[oa]s?|privad[oa]s?|urgencias|cardiolog|pediatr)|$|,)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" ,.-")
            if len(candidate) >= 3:
                return candidate
    return ""
