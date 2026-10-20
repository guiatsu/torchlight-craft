"""Data-backed validation, with unknown rules kept explicit."""

from __future__ import annotations

from collections import Counter

from core.models import (
    MAX_ITEM_LEVEL,
    MIN_ITEM_LEVEL,
    AffixDefinition,
    BaseDefinition,
    EquipmentItem,
    resolve_tier_reference,
)


def _canonical_family_candidates(instance, affixes: dict[str, AffixDefinition]) -> set[str]:
    definition = affixes.get(instance.definition_id)
    if definition is None or not definition.is_legacy_alias or not definition.legacy_family_member_ids:
        return {instance.definition_id}
    tier, ambiguous = resolve_tier_reference(definition.tiers, instance.tier_id)
    if ambiguous:
        return set(definition.legacy_family_member_ids)
    if tier is not None:
        matching = [
            member_id for member_id in definition.legacy_family_member_ids
            if member_id in affixes and any(option.id == tier.id for option in affixes[member_id].tiers)
        ]
        if len(matching) == 1:
            return {matching[0]}
    return set(definition.legacy_family_member_ids)


def validate_item(
    item: EquipmentItem,
    bases: dict[str, BaseDefinition],
    affixes: dict[str, AffixDefinition],
) -> list[str]:
    errors: list[str] = []
    if not item.name.strip():
        errors.append("Give this equipment a name.")
    if len(item.name) > 80:
        errors.append("Equipment names must be 80 characters or fewer.")
    if isinstance(item.item_level, bool) or not isinstance(item.item_level, int):
        errors.append("Item Level must be a whole number.")
    elif not MIN_ITEM_LEVEL <= item.item_level <= MAX_ITEM_LEVEL:
        errors.append(f"Item Level must be between {MIN_ITEM_LEVEL} and {MAX_ITEM_LEVEL}.")

    base = bases.get(item.base_id)
    if base is None:
        errors.append("The selected equipment base is not in the local catalog.")
    elif base.minimum_item_level is not None and item.item_level < base.minimum_item_level:
        errors.append(f"This base requires at least Item Level {base.minimum_item_level} in the current catalog.")

    instance_ids = [affix.id for affix in item.affixes]
    if len(instance_ids) != len(set(instance_ids)):
        errors.append("Each affix needs a unique instance ID.")

    family_instances: dict[str, set[str]] = {}
    for instance in item.affixes:
        for family_id in _canonical_family_candidates(instance, affixes):
            family_instances.setdefault(family_id, set()).add(instance.id)
    duplicate_family_ids = {
        family_id for family_id, instance_ids in family_instances.items() if len(instance_ids) > 1
    }
    for family_id in sorted(duplicate_family_ids):
        definition = affixes.get(family_id)
        name = definition.name if definition else family_id
        errors.append(f"{name} can only be added once to an equipment item.")

    counts = Counter(affix.group.value for affix in item.affixes)
    if base is not None:
        for group, limit in (("prefix", base.prefix_limit), ("suffix", base.suffix_limit)):
            if limit is not None and counts[group] > limit:
                errors.append(f"This base has a provisional {group} limit of {limit}.")

    for instance in item.affixes:
        definition = affixes.get(instance.definition_id)
        if definition is None:
            errors.append(f"Affix {instance.id} refers to an unknown catalog entry.")
            continue
        if definition.group != instance.group:
            errors.append(f"Affix {definition.name} is stored in the wrong group.")
        if definition.category != instance.category:
            errors.append(f"Affix {definition.name} has a category that does not match the catalog.")
        if base is not None and definition.base_ids and base.id not in definition.base_ids:
            errors.append(f"Affix {definition.name} is not listed for {base.name}.")
        tier, ambiguous_tier = resolve_tier_reference(definition.tiers, instance.tier_id)
        if tier is None:
            if ambiguous_tier:
                errors.append(
                    f"Affix {definition.name} has an ambiguous legacy tier label {instance.tier_id}; choose a specific tier record."
                )
            else:
                errors.append(f"Affix {definition.name} has an unsupported tier.")
        elif tier.item_level_required is not None and item.item_level < tier.item_level_required:
            errors.append(
                f"Affix {definition.name} {tier.tier_label} is listed from Item Level {tier.item_level_required}."
            )
        if len(instance.value) > 120:
            errors.append(f"Affix {definition.name} value must be 120 characters or fewer.")

    return errors
