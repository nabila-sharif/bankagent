
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

# ---------------- Gemini Settings ----------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY



if not GEMINI_API_KEY:
    raise ValueError("⚠ GEMINI_API_KEY not found in .env file.")

# ---------------- Tool Decorator ----------------
def function_tool(func):
    func.is_tool = True
    return func

# ---------------- Tools ----------------
@function_tool
def check_balance(account_number: str) -> str:
    return f"The balance of account {account_number} is $1,000,000.00"

# ---------------- Agent Class ----------------
class Agent:
    def __init__(self, name, instructions, tools=None):
        self.name = name
        self.instructions = instructions
        self.tools = {t.__name__: t for t in (tools or [])}

    def run(self, user_message):
        # Step 1: Ask Gemini if a tool should be used
        tool_call = self._ask_gemini_for_tool(user_message)

        if tool_call and tool_call["name"] in self.tools:
            tool_func = self.tools[tool_call["name"]]
            args = tool_call.get("arguments", {})
            tool_result = tool_func(**args)

            # Step 2: Send result back to Gemini for final answer
            final_prompt = (
                f"User asked: {user_message}\n"
                f"Tool used: {tool_call['name']}\n"
                f"Tool result: {tool_result}\n"
                f"Respond politely and clearly."
            )
            return self._call_gemini(final_prompt)

        # No tool needed → directly ask Gemini
        return self._call_gemini(f"{self.instructions}\nUser: {user_message}")

    def _ask_gemini_for_tool(self, user_message):
        """Ask Gemini to decide if a tool should be called"""
        tool_list = ", ".join(
            [f"{name}({', '.join(func.__code__.co_varnames)})" for name, func in self.tools.items()]
        )

        prompt = f"""
You are an AI agent with these tools:
{tool_list}

User message: "{user_message}"

If a tool should be called, respond ONLY in valid JSON like:
{{"name": "tool_name", "arguments": {{"arg1": "value"}}}}
If no tool is needed, respond with: null
"""
        reply = self._call_gemini(prompt)
        try:
            return json.loads(reply)
        except:
            return None

    def _call_gemini(self, prompt):
        """Send a request to Gemini API"""
        headers = {"Content-Type": "application/json"}
        params = {"key": GEMINI_API_KEY}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=data)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

# ---------------- Runner Class ----------------
class Runner:
    @staticmethod
    def run_sync(agent, message):
        result = agent.run(message)
        return type("Result", (), {"final_output": result})

# ---------------- Create & Run Agent ----------------
bankagent = Agent(
    name="Bank Agent",
    instructions="You are a helpful bank agent. Use tools when needed.",
    tools=[check_balance]
)

result = Runner.run_sync(bankagent, "I want to check my account balance for account_number 12345")
print(result.final_output) 