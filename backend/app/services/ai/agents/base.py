"""An 'agent' in HippocampusFlow is deliberately simple: a name, a system
prompt, and a shared output contract. All agents must reply with JSON:

  {"summary": "...", "details": {...}, "suggested_actions": [...],
   "memory": "<one sentence to remember>"}

The memory sentence is what makes the app remember: it gets stored and fed
into future analyses ("this is the same brand of coffee you scanned in
March"). Adding a new specialist = one new file defining a Prompt.
"""
from dataclasses import dataclass

OUTPUT_CONTRACT = """Respond with ONLY a JSON object, no other text:
{"summary": "<2-4 sentences a curious person would find genuinely useful>",
 "details": {"<short label>": "<short value>", ...},
 "suggested_actions": ["<short action the user might want>", ...],
 "memory": "<ONE short factual sentence worth remembering about this scan,
written in third person about the user, e.g. 'User owns a blue ceramic mug'>"}
Keep details to at most 6 entries and suggested_actions to at most 4."""


@dataclass(frozen=True)
class Agent:
    name: str
    system_prompt: str
