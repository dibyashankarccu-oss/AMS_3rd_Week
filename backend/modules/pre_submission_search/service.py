from core.constants import (
    HISTORICAL_VECTOR_THRESHOLD,
    HISTORICAL_LLM_THRESHOLD
)


def filter_candidates(results):

    if not results:
        return []

    return [

        r for r in results

        if r.get(
            "similarity",
            0
        ) >= HISTORICAL_VECTOR_THRESHOLD
    ]


def is_valid_match(ticket):

    if not ticket:
        return False

    return (

        ticket.get(
            "llm_score",
            0
        )

        >=

        HISTORICAL_LLM_THRESHOLD
    )