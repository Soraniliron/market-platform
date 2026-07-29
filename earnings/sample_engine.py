def get_sample_status(
    cycles_count: int,
    minimum_cycles_required: int,
) -> str:
    if cycles_count < 0:
        raise ValueError(
            "cycles_count must not be negative"
        )

    if minimum_cycles_required < 1:
        raise ValueError(
            "minimum_cycles_required must be at least one"
        )

    if cycles_count >= 30:
        return "SEASONAL_READY"

    if cycles_count >= 20:
        return "STABILITY_READY"

    if cycles_count >= minimum_cycles_required:
        return "PRODUCTION_READY"

    if cycles_count >= 4:
        return "RESEARCH_ONLY"

    return "INSUFFICIENT_SAMPLE"


def is_production_ready(
    cycles_count: int,
    minimum_cycles_required: int = 12,
) -> bool:
    if cycles_count < 0:
        raise ValueError(
            "cycles_count must not be negative"
        )

    if minimum_cycles_required < 1:
        raise ValueError(
            "minimum_cycles_required must be at least one"
        )

    return cycles_count >= minimum_cycles_required
