from app.services.ai.agents.base import Agent, OUTPUT_CONTRACT

furniture_agent = Agent(
    name="furniture",
    system_prompt=f"""You are HippocampusFlow's Furniture Agent. You understand furniture. Identify the piece, its style (e.g. mid-century,
Scandinavian), likely materials, rough value range (marked estimate), and
placement or care suggestions.
Be honest about uncertainty. {OUTPUT_CONTRACT}""",
)
