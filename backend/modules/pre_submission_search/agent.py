import re
import asyncio

from services.llm_service import call_llm
from .prompt import HISTORY_MATCH_PROMPT


def parse_score(text):

    print("RAW LLM:", text)

    if not text:
        return 0

    m = re.search(
        r'(\d+)',
        str(text)
    )

    if not m:
        return 0

    score=int(m.group(1))

    return max(
        0,
        min(score,100)
    )


async def compare_ticket(
    summary,
    description,
    candidate
):

    # exact match shortcut
    if (
        summary.strip().lower()
        ==
        candidate.get(
            "summary",
            ""
        ).strip().lower()
    ):

        print(
            "EXACT SUMMARY MATCH:",
            candidate["issue_key"]
        )

        return {
            **candidate,
            "llm_score":100
        }

    prompt=HISTORY_MATCH_PROMPT.format(

        summary=summary,
        description=description,

        existing_summary=
            candidate.get(
                "summary",
                ""
            ),

        existing_description=
            candidate.get(
                "description",
                ""
            )
    )

    try:

        res=await call_llm(
            prompt
        )

        score=parse_score(
            res
        )

        print(
            candidate["issue_key"],
            "LLM:",
            score
        )

        return {
            **candidate,
            "llm_score":score
        }

    except Exception as e:

        print(
            "LLM error:",
            e
        )

        return {
            **candidate,
            "llm_score":0
        }


async def rerank_tickets(
    summary,
    description,
    tickets
):

    if not tickets:
        return None

    tasks=[

        compare_ticket(
            summary,
            description,
            t
        )

        for t in tickets
    ]

    results=await asyncio.gather(
        *tasks
    )

    results.sort(

        key=lambda x:
            x["llm_score"],

        reverse=True
    )

    print("\nRERANKED:")

    for r in results:

        print(
            r["issue_key"],
            r["llm_score"]
        )

    return results[0]