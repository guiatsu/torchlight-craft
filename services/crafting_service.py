"""Session-local facade and bounded pool cache for the pure craft engine."""

from __future__ import annotations

from collections import OrderedDict

from core.catalog import Catalog
from core.crafting import CraftAction, CraftPool, CraftResult, CraftingEngine, CraftingError
from core.models import EquipmentItem


class CraftingService:
    def __init__(self, catalog: Catalog, cache_size: int = 128) -> None:
        self.engine = CraftingEngine(catalog)
        self._cache_size = cache_size
        self._pool_cache: OrderedDict[tuple[object, ...], CraftPool | str] = OrderedDict()

    @staticmethod
    def _key(item: EquipmentItem, action: CraftAction) -> tuple[object, ...]:
        affixes = tuple(
            (entry.id, entry.definition_id, entry.group.value, entry.category.value, entry.tier_id)
            for entry in item.affixes
        )
        return (
            item.base_id,
            item.item_level,
            item.priceless,
            action.group.value,
            action.slot_index,
            action.category.value,
            action.model_id,
            action.experimental_opt_in,
            affixes,
        )

    def preview(self, item: EquipmentItem, action: CraftAction) -> CraftPool:
        key = self._key(item, action)
        cached = self._pool_cache.get(key)
        if cached is not None:
            self._pool_cache.move_to_end(key)
            if isinstance(cached, str):
                raise CraftingError(cached)
            return cached
        try:
            pool = self.engine.build_pool(item, action)
            value: CraftPool | str = pool
        except CraftingError as exc:
            value = str(exc)
            self._pool_cache[key] = value
            self._trim_cache()
            raise
        self._pool_cache[key] = value
        self._trim_cache()
        return pool

    def attempt(self, item: EquipmentItem, action: CraftAction) -> CraftResult:
        return self.engine.attempt(item, action)

    def invalidate(self) -> None:
        self._pool_cache.clear()

    def _trim_cache(self) -> None:
        while len(self._pool_cache) > self._cache_size:
            self._pool_cache.popitem(last=False)
