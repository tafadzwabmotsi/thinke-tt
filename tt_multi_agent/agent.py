import os
import asyncio
from agents import FunctionTool
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import warnings
import logging
from typing import Optional

from tt_multi_agent.guardrails import block_keyword_guardrail, block_paris_tool_guardrail
from tt_multi_agent.tooling import get_weather_stateful
from tt_multi_agent.tools.farewell_tools import FarewellTools
from tt_multi_agent.tools.greeting_tools import GreetingTools 


warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.ERROR)

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

# Initialize New Session Service and State
session_service_stateful = InMemorySessionService()
print("✅ New InMemorySessionService created for state demonstration.")

# Define a NEW session ID for this part of the tutorial
SESSION_ID_STATEFUL = "session_state_demo_001"
USER_ID_STATEFUL = "user_state_demo"
APP_NAME = "stateful_session_agents"


# Define initial state data - user prefers Celsius initially
initial_state = {
    "user_preference_temperature_unit": "Celsius"
}

# Define tool objects
greeting_tools = GreetingTools()
farewell_tools = FarewellTools()


# --- Greeting Agent ---
greeting_agent = None
try:
    greeting_agent = Agent(
        # Using a potentially different/cheaper model for a simple task
        model = MODEL_GEMINI_2_0_FLASH,
        # model=LiteLlm(model=MODEL_GPT_4O), # If you would like to experiment with other models
        name="greeting_agent",
        instruction="You are the Greeting Agent. Your ONLY task is to provide a friendly greeting to the user. "
                    "Use the 'say_hello' tool to generate the greeting. "
                    "If the user provides their name, make sure to pass it to the tool. "
                    "Do not engage in any other conversation or tasks.",
        description="Handles simple greetings and hellos using the 'say_hello' tool.", # Crucial for delegation
        tools=[FunctionTool(func=greeting_tools.say_hello)],
    )
    print(f"✅ Agent '{greeting_agent.name}' created using model '{greeting_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create Greeting agent. Check API Key ({greeting_agent.model}). Error: {e}")


# --- Farewell Agent ---
farewell_agent = None
try:
    farewell_agent = Agent(
        # Can use the same or a different model
        model = MODEL_GEMINI_2_0_FLASH,
        # model=LiteLlm(model=MODEL_GPT_4O), # If you would like to experiment with other models
        name="farewell_agent",
        instruction="You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message. "
                    "Use the 'say_goodbye' tool when the user indicates they are leaving or ending the conversation "
                    "(e.g., using words like 'bye', 'goodbye', 'thanks bye', 'see you'). "
                    "Do not perform any other actions.",
        description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.", # Crucial for delegation
        tools=[FunctionTool()],
    )
    print(f"✅ Agent '{farewell_agent.name}' created using model '{farewell_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create Farewell agent. Check API Key ({farewell_agent.model}). Error: {e}")
    

# --- Define the Updated Root Agent ---
root_agent = None
runner_root_stateful = None

# --- Define the Root Agent with the Callback ---
root_agent = None
runner_root_model_guardrail = None

# Check all components before proceeding
if greeting_agent and farewell_agent and get_weather_stateful and block_keyword_guardrail:

    # Use a defined model constant
    root_agent_model = MODEL_GEMINI_2_0_FLASH

    root_agent = Agent(
        name="weather_agent_v6_tool_guardrail", # New version name for clarity
        model=root_agent_model,
        description="Main agent: Handles weather, delegates greetings/farewells, includes input keyword guardrail.",
        instruction="You are the main Weather Agent. Provide weather using 'get_weather_stateful'. "
                    "Delegate simple greetings to 'greeting_agent' and farewells to 'farewell_agent'. "
                    "Handle only weather requests, greetings, and farewells.",
        tools=[get_weather_stateful],
        sub_agents=[greeting_agent, farewell_agent],
        output_key="last_weather_report",
        before_model_callback=block_keyword_guardrail, # Keep model guardrail
        before_tool_callback=block_paris_tool_guardrail # <<< Add tool guardrail
    )
    print(f"✅ Root Agent '{root_agent.name}' created with BOTH callbacks.")

    # --- Create Runner, Using SAME Stateful Session Service ---
    if 'session_service_stateful' in globals():
        runner_root_tool_guardrail = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service_stateful # <<< Use the service from Step 4/5
        )
        print(f"✅ Runner created for tool guardrail agent '{runner_root_tool_guardrail.agent.name}', using stateful session service.")
    else:
        print("❌ Cannot create runner. 'session_service_stateful' from Step 4/5 is missing.")

else:
    print("❌ Cannot create root agent with tool guardrail. Prerequisites missing.")

async def call_agent_async(query: str, runner, user_id, session_id):
    """Sends a query to the agent and prints the final response."""
    print(f"\n>>> User Query: {query}")

    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response." # Default

    # Key Concept: run_async executes the agent logic and yields Events.
    # We iterate through events to find the final answer.
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # You can uncomment the line below to see *all* events during execution
        # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

        # Key Concept: is_final_response() marks the concluding message for the turn.
        if event.is_final_response():
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
            # Add more checks here if needed (e.g., specific error codes)
            break # Stop processing events once the final response is found

    print(f"<<< Agent Response: {final_response_text}")
  
    # Ensure the runner for the guardrail agent is available
    if 'runner_root_model_guardrail' in globals() and runner_root_model_guardrail:
        # Define the main async function for the guardrail test conversation.
        # The 'await' keywords INSIDE this function are necessary for async operations.
        async def run_guardrail_test_conversation():
            print("\n--- Testing Model Input Guardrail ---")

            # Use the runner for the agent with the callback and the existing stateful session ID
            # Define a helper lambda for cleaner interaction calls
            interaction_func = lambda query: call_agent_async(query,
                                                            runner_root_model_guardrail,
                                                            USER_ID_STATEFUL, # Use existing user ID
                                                            SESSION_ID_STATEFUL # Use existing session ID
                                                            )
            # 1. Normal request (Callback allows, should use Fahrenheit from previous state change)
            print("--- Turn 1: Requesting weather in London (expect allowed, Fahrenheit) ---")
            await interaction_func("What is the weather in London?")

            # 2. Request containing the blocked keyword (Callback intercepts)
            print("\n--- Turn 2: Requesting with blocked keyword (expect blocked) ---")
            await interaction_func("BLOCK the request for weather in Tokyo") # Callback should catch "BLOCK"

            # 3. Normal greeting (Callback allows root agent, delegation happens)
            print("\n--- Turn 3: Sending a greeting (expect allowed) ---")
            await interaction_func("Hello again")
      
        await run_guardrail_test_conversation()


async def main():
    # Create the session, providing the initial state
    session_stateful = await session_service_stateful.create_session(
        app_name=APP_NAME, # Use the consistent app name
        user_id=USER_ID_STATEFUL,
        session_id=SESSION_ID_STATEFUL,
        state=initial_state # <<< Initialize state during creation
    )
    print(f"✅ Session '{SESSION_ID_STATEFUL}' created for user '{USER_ID_STATEFUL}'.")

    # Verify the initial state was set correctly
    retrieved_session = await session_service_stateful.get_session(app_name=APP_NAME,
                                                            user_id=USER_ID_STATEFUL,
                                                            session_id = SESSION_ID_STATEFUL)
    print("\n--- Initial Session State ---")
    if retrieved_session:
        print(retrieved_session.state)
    else:
        print("Error: Could not retrieve session.")
      
    if 'runner_root_stateful' in globals() and runner_root_stateful:
        # Define the main async function for the stateful conversation logic.
        # The 'await' keywords INSIDE this function are necessary for async operations.
        async def run_stateful_conversation():
            print("\n--- Testing State: Temp Unit Conversion & output_key ---")

            # 1. Check weather (Uses initial state: Celsius)
            print("--- Turn 1: Requesting weather in London (expect Celsius) ---")
            await call_agent_async(query= "What's the weather in London?",
                                runner=runner_root_stateful,
                                user_id=USER_ID_STATEFUL,
                                session_id=SESSION_ID_STATEFUL
                                )

            # 2. Manually update state preference to Fahrenheit - DIRECTLY MODIFY STORAGE
            print("\n--- Manually Updating State: Setting unit to Fahrenheit ---")
            try:
                # Access the internal storage directly - THIS IS SPECIFIC TO InMemorySessionService for testing
                # NOTE: In production with persistent services (Database, VertexAI), you would
                # typically update state via agent actions or specific service APIs if available,
                # not by direct manipulation of internal storage.
                stored_session = session_service_stateful.sessions[APP_NAME][USER_ID_STATEFUL][SESSION_ID_STATEFUL]
                stored_session.state["user_preference_temperature_unit"] = "Fahrenheit"
                # Optional: You might want to update the timestamp as well if any logic depends on it
                # import time
                # stored_session.last_update_time = time.time()
                print(f"--- Stored session state updated. Current 'user_preference_temperature_unit': {stored_session.state.get('user_preference_temperature_unit', 'Not Set')} ---") # Added .get for safety
            except KeyError:
                print(f"--- Error: Could not retrieve session '{SESSION_ID_STATEFUL}' from internal storage for user '{USER_ID_STATEFUL}' in app '{APP_NAME}' to update state. Check IDs and if session was created. ---")
            except Exception as e:
                print(f"--- Error updating internal session state: {e} ---")

            # 3. Check weather again (Tool should now use Fahrenheit)
            # This will also update 'last_weather_report' via output_key
            print("\n--- Turn 2: Requesting weather in New York (expect Fahrenheit) ---")
            await call_agent_async(query= "Tell me the weather in New York.",
                                runner=runner_root_stateful,
                                user_id=USER_ID_STATEFUL,
                                session_id=SESSION_ID_STATEFUL
                                )

            # 4. Test basic delegation (should still work)
            # This will update 'last_weather_report' again, overwriting the NY weather report
            print("\n--- Turn 3: Sending a greeting ---")
            await call_agent_async(query= "Hi!",
                                runner=runner_root_stateful,
                                user_id=USER_ID_STATEFUL,
                                session_id=SESSION_ID_STATEFUL
                                )

        await run_stateful_conversation()


if __name__ == "__main__":
    asyncio.run(main())