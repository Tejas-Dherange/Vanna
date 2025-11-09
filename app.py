from vanna import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool, SaveTextMemoryTool
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.integrations.google import GeminiLlmService
from vanna.integrations.postgres import PostgresRunner  # Changed from SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure your LLM
llm = GeminiLlmService(
    model="gemini-2.5-flash",  # Using a more available model
    api_key=os.getenv("GOOGLE_API_KEY")  # Make sure this is set in your .env
)

# Configure your PostgreSQL database
# Alternative PostgreSQL configuration using connection string
db_tool = RunSqlTool(
    sql_runner=PostgresRunner(
        connection_string=os.getenv("DATABASE_URL")  # postgresql://user:password@host:port/database
    )
)

# Configure your agent memory
agent_memory = DemoAgentMemory(max_items=1000)

# Configure user authentication
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        user_email = request_context.get_cookie('vanna_email') or 'guest@example.com'
        group = 'admin' if user_email == 'admin@example.com' else 'user'
        return User(id=user_email, email=user_email, group_memberships=[group])

user_resolver = SimpleUserResolver()

# Create your agent
tools = ToolRegistry()
tools.register_local_tool(db_tool, access_groups=['admin', 'user'])
tools.register_local_tool(SaveQuestionToolArgsTool(), access_groups=['admin'])
tools.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=['admin', 'user'])
tools.register_local_tool(SaveTextMemoryTool(), access_groups=['admin', 'user'])
tools.register_local_tool(VisualizeDataTool(), access_groups=['admin', 'user'])

agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=user_resolver,
    agent_memory=agent_memory
)

# Run the server
if __name__ == "__main__":
    server = VannaFastAPIServer(agent)
    server.run()