"""Public catalog entry point; loading is deferred to avoid import-time cycles.

Use typed search filters for eligibility; selection and party assembly belong to
request handlers above the catalog.
"""

from importlib import import_module

_EXPORTS = {
    "CatalogSearchService": (".search", "CatalogSearchService"),
    "MonsterSearchFilters": (".search", "MonsterSearchFilters"),
    "MonsterCatalogBootstrapService": (".bootstrap", "MonsterCatalogBootstrapService"),
    "get_catalog": (".registry", "get_catalog"),
}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attribute = _EXPORTS[name]
    value = getattr(import_module(module, __name__), attribute)
    globals()[name] = value
    return value
