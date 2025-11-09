from typing import Dict, List, Any
from vanna.integrations.local.agent_memory import DemoAgentMemory

class InMemoryStore(DemoAgentMemory):
    def __init__(self, max_items: int = 1000):
        super().__init__(max_items=max_items)
        self.memory = {'tools': [], 'text': []}