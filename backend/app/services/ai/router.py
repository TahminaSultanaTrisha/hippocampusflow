"""The AI Router: category -> specialist agent.
The full roster. Adding an agent = one file in agents/ + one line here."""
from app.services.ai.agents.base import Agent
from app.services.ai.agents.animal import animal_agent
from app.services.ai.agents.appliance import appliance_agent
from app.services.ai.agents.artwork import artwork_agent
from app.services.ai.agents.cooking import cooking_agent
from app.services.ai.agents.document import document_agent
from app.services.ai.agents.electronics import electronics_agent
from app.services.ai.agents.fashion import fashion_agent
from app.services.ai.agents.food import food_agent
from app.services.ai.agents.furniture import furniture_agent
from app.services.ai.agents.general import general_agent
from app.services.ai.agents.insect import insect_agent
from app.services.ai.agents.mineral import mineral_agent
from app.services.ai.agents.plant import plant_agent
from app.services.ai.agents.product import product_agent
from app.services.ai.agents.receipt import receipt_agent
from app.services.ai.agents.repair import repair_agent
from app.services.ai.agents.travel import travel_agent
from app.services.ai.agents.vehicle import vehicle_agent

AGENTS: dict[str, Agent] = {
    "receipt": receipt_agent,
    "product": product_agent,
    "food": food_agent,
    "ingredients": cooking_agent,
    "electronics": electronics_agent,
    "clothing": fashion_agent,
    "furniture": furniture_agent,
    "appliance": appliance_agent,
    "household": appliance_agent,
    "document": document_agent,
    "plant": plant_agent,
    "animal": animal_agent,
    "insect": insect_agent,
    "vehicle": vehicle_agent,
    "artwork": artwork_agent,
    "landmark": travel_agent,
    "mineral": mineral_agent,
    "damage": repair_agent,
}


def route(category: str) -> Agent:
    return AGENTS.get(category, general_agent)
