RUNBOOK_CHECKLIST_PROMPT = """You are a senior IT Site Reliability Engineer.

An incident ticket has been received:
  Summary     : {summary}
  Description : {description}

The most relevant runbook for this incident is:
  Title      : {runbook_title}
  Category   : {runbook_category}
  Symptoms   : {runbook_symptoms}

Reference resolution steps from the runbook:
{runbook_steps}

Your task — produce a structured checklist where EACH step may have an optional command.

Format EXACTLY as below. Each step starts with "STEP:" on its own line.
If a step has a shell command, put it on the VERY NEXT LINE starting with "CMD:".
If a step has no command, do NOT include a CMD line — go straight to the next STEP.
Maximum 8 steps. Only safe, read-only or restart commands — never destructive ones.

Output format (no extra text, no markdown):
STEP: <step text>
CMD: <optional shell command for this step>
STEP: <step text>
STEP: <step text>
CMD: <optional shell command for this step>
...
"""

FALLBACK_CHECKLIST_PROMPT = """You are a senior IT Site Reliability Engineer.

An incident ticket has been received with NO matching runbook:
  Summary     : {summary}
  Description : {description}

Generate a practical troubleshooting checklist where EACH step may have an optional command.

Format EXACTLY as below. Each step starts with "STEP:" on its own line.
If a step has a shell command, put it on the VERY NEXT LINE starting with "CMD:".
If a step has no command, do NOT include a CMD line — go straight to the next STEP.
Maximum 6 steps. Only safe diagnostic commands.

Output format (no extra text, no markdown):
STEP: <step text>
CMD: <optional shell command for this step>
STEP: <step text>
STEP: <step text>
CMD: <optional shell command for this step>
...
"""