from typing import TypedDict, List
import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

# Define the structure for a single scene in the video
class VideoScene(TypedDict):
    visual_query: str
    text_overlay: str
    script: str
    duration: int

# Define the state of our agent
class AgentState(TypedDict):
    user_request: str
    timeline: List[VideoScene]

class VideoDirector:
    def __init__(self):
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Using a model capable of good JSON output
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        self.graph = self._build_graph()

    def _build_graph(self):
        def parse_request(state: AgentState):
            print("   Drafting detailed timeline...")
            request = state['user_request']
            
            system_prompt = """You are an expert World-Class Dog Trainer and Cinematographer.
            Your goal is to create viral, highly accurate YouTube Shorts about dogs.
            
            The output must be a JSON array of objects, where each object represents a scene:
            [
                {
                    "visual_query": "string (EXACT PEXELS SEARCH TERM)",
                    "text_overlay": "string (short, punchy text)",
                    "script": "string (narration)",
                    "duration": int (seconds)
                }
            ]
            
            CRITICAL RULES:
            1. **Visual Consistency**: The `visual_query` MUST be a specific search term for stock footage. 
               - ALWAYS append "dog" to the query. 
               - If the script mentions a specific breed (e.g., "Golden Retriever"), the visual_query MUST include "Golden Retriever".
               - Example: "Golden Retriever running in park", "Golden Retriever close up face".
               - Avoid generic terms like "happiness" or "loyalty" -> Convert to visual: "dog looking happy", "dog licking owner".
               - If the script is about "Pooping", search for "dog squatting grass" or "dog spinning".
            2. **No Humans (Unless necessary)**: Prefer shots of just the dog unless the script implies interaction.
            3. **Text Overlay**: 1-3 words max. BIG & BOLD.
            4. **Script**: Keep it punchy, fast-paced (YouTube Shorts style).
            """
            
            user_prompt = f"Create a video timeline based on this request:\n\n{request}"
            
            # Force JSON mode by prompting (Gemini is good at this, but explicit instruction helps)
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt + "\n\nReturn ONLY the valid JSON array.")
            ])
            
            content = response.content.replace('```json', '').replace('```', '').strip()
            try:
                timeline = json.loads(content)
            except json.JSONDecodeError:
                print("   ⚠️ LLM failed to return valid JSON. Retrying or using fallback logic might be needed.")
                print(f"   Raw Output: {content}")
                timeline = []

            return {"timeline": timeline}

        # Build Graph
        workflow = StateGraph(AgentState)
        workflow.add_node("planner", parse_request)
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", END)

        return workflow.compile()

    def generate_script(self, user_request: str):
        """
        Runs the workflow to generate the video timeline.
        """
        initial_state = {"user_request": user_request, "timeline": []}
        result = self.graph.invoke(initial_state)
        return result
