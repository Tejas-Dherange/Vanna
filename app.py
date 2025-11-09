import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from vanna import Agent
    from vanna.core.registry import ToolRegistry
    from vanna.core.user import UserResolver, User, RequestContext
    from vanna.tools import RunSqlTool, VisualizeDataTool
    from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool, SaveTextMemoryTool
    from vanna.servers.fastapi import VannaFastAPIServer
    from vanna.integrations.google import GeminiLlmService
    from vanna.integrations.postgres import PostgresRunner
    from vanna.integrations.local.agent_memory import DemoAgentMemory
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install required packages:")
    print("pip install 'vanna[fastapi,gemini] @ git+https://github.com/vanna-ai/vanna.git@v2' psycopg2-binary python-dotenv")
    exit(1)

def main():
    # Validate required environment variables
    google_api_key = os.getenv("GOOGLE_API_KEY")
    database_url = os.getenv("DATABASE_URL")
    
    if not google_api_key:
        print("❌ Missing GOOGLE_API_KEY environment variable")
        print("   Please set it in your .env file")
        return
        
    if not database_url:
        print("❌ Missing DATABASE_URL environment variable")
        print("   Please set it in your .env file in the format:")
        print("   DATABASE_URL=postgresql://username:password@localhost:5432/your_database_name")
        return

    # Configure your LLM
    try:
        llm = GeminiLlmService(
            model="gemini-2.5-flash",  # You can also use "gemini-1.5-pro" or "gemini-2.0-flash-exp"
            api_key=google_api_key
        )
        print("✅ Google Gemini LLM configured successfully")
    except Exception as e:
        print(f"❌ LLM configuration error: {e}")
        return

    # Configure your PostgreSQL database using connection string
    try:
        db_tool = RunSqlTool(
            sql_runner=PostgresRunner(connection_string=database_url)
        )
        print("✅ PostgreSQL connection configured successfully")
        
        # Test the database connection
        test_result = db_tool.sql_runner.run_sql("SELECT 1 as test", {})  # Empty context dictionary
        print("✅ Database connection test passed")
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("   Please check your DATABASE_URL format and ensure PostgreSQL is running")
        print("   Format should be: postgresql://username:password@host:port/database")
        return

    # Configure your agent memory
    agent_memory = DemoAgentMemory(max_items=1000)
    print("✅ Agent memory configured")

    # Configure user authentication
    class SimpleUserResolver(UserResolver):
        async def resolve_user(self, request_context: RequestContext) -> User:
            user_email = request_context.get_cookie('vanna_email') or 'guest@example.com'
            group = 'admin' if user_email == 'admin@example.com' else 'user'
            return User(id=user_email, email=user_email, group_memberships=[group])

    user_resolver = SimpleUserResolver()
    print("✅ User resolver configured")

    # Create your agent with tool registry
    tools = ToolRegistry()
    
    # Register tools with appropriate access groups
    tools.register_local_tool(db_tool, access_groups=['admin', 'user'])
    tools.register_local_tool(SaveQuestionToolArgsTool(), access_groups=['admin'])
    tools.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=['admin', 'user'])
    tools.register_local_tool(SaveTextMemoryTool(), access_groups=['admin', 'user'])
    tools.register_local_tool(VisualizeDataTool(), access_groups=['admin', 'user'])
    
    print("✅ Tools registered successfully")

    # Create the agent
    agent = Agent(
        llm_service=llm,
        tool_registry=tools,
        user_resolver=user_resolver,
        agent_memory=agent_memory
    )
    print("✅ Vanna Agent created successfully")

    # Run the server
    print("\n🚀 Starting Vanna FastAPI Server...")
    print("=" * 50)
    print("📊 Database: PostgreSQL (via connection string)")
    print("🤖 LLM: Google Gemini")
    print("🌐 Server URL: http://localhost:8080")
    print("📚 API Documentation: http://localhost:8080/docs")
    print("🛠️  Health Check: http://localhost:8080/health")
    print("=" * 50)
    print("Press Ctrl+C to stop the server\n")
    
    server = VannaFastAPIServer(agent)
    server.run()

if __name__ == "__main__":
    main()