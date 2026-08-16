import importlib
import logging
import pkgutil
from pathlib import Path

from plugins.base import CalculatorPlugin, InputField, CalcResult

__all__ = [
    "CalculatorPlugin",
    "InputField",
    "CalcResult",
    "discover_plugins",
    "get_all_plugins",
    "get_plugin",
    "get_plugins_by_category",
]

logger = logging.getLogger(__name__)

_registry: dict[str, CalculatorPlugin] = {}
_discovered = False


def discover_plugins() -> dict[str, CalculatorPlugin]:
    global _discovered, _registry

    _registry.clear()
    package_dir = Path(__file__).parent

    for _importer, module_name, _is_pkg in pkgutil.iter_modules([str(package_dir)]):
        if module_name in ("base", "__init__"):
            continue
        try:
            module = importlib.import_module(f"plugins.{module_name}")
        except Exception:
            logger.exception("Failed to import plugin module: %s", module_name)
            continue

        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if (
                isinstance(obj, type)
                and issubclass(obj, CalculatorPlugin)
                and obj is not CalculatorPlugin
            ):
                try:
                    instance = obj()
                    if instance.name in _registry:
                        logger.warning(
                            "Duplicate plugin name '%s' from module '%s'. "
                            "Keeping first registration.",
                            instance.name,
                            module_name,
                        )
                        continue
                    _registry[instance.name] = instance
                    logger.debug("Registered plugin: %s", instance.name)
                except Exception:
                    logger.exception(
                        "Failed to instantiate plugin class %s from %s",
                        attr_name,
                        module_name,
                    )

    _discovered = True
    logger.info("Plugin discovery complete. %d plugin(s) registered.", len(_registry))
    return dict(_registry)


def get_all_plugins() -> dict[str, CalculatorPlugin]:
    if not _discovered:
        discover_plugins()
    return dict(_registry)


def get_plugin(name: str) -> CalculatorPlugin | None:
    return get_all_plugins().get(name)


def get_plugins_by_category(category: str) -> list[CalculatorPlugin]:
    return [p for p in get_all_plugins().values() if p.category == category]
