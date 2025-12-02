import os
import asyncio
import json
import re
from pydantic import BaseModel, Field, ValidationError
from typing import List
from google import genai
from google.genai import types
from dotenv import load_dotenv

from TravelTools import TravelTools, LongTermMemoryTool, SchedulerTools
from schemas import *

# F: 
def run_scheduler_agent(final_itinerary: List[DailyPlan], start_date: str) -> BookingConfirmation | None:
    """
    The scheduling and booking agent processes the itinerary and converts it into simulated booking confirmations.
    
    :param final_itinerary: The generated DailyPlan list.
    :param start_date: The actual start date of the travel (e.g., “2025-12-01”).
    :returns: The BookingConfirmation object confirms simulated bookings.
    """
    if not client: return None
    
    # 1. Convert the final itinerary to LLM text.
    itinerary_text = json.dumps([p.model_dump() for p in final_itinerary], ensure_ascii=False)
    
    # 2. Formulating the Request
    system_prompt = (
        "You are The Scheduler Agent. Your task is to finalize the travel itinerary by simulating "
        "the booking of all planned activities and generating a **BookingConfirmation** JSON object. "
        "You must generate unique, realistic-sounding confirmation codes (e.g., 'CAI789-F') "
        "and booking times for each activity. The total cost must reflect the sum of the estimated daily costs from the itinerary. "
        "Your output MUST be a clean JSON object that strictly follows the provided Pydantic schema."
        f"\nSchema: {BookingConfirmation.model_json_schema()}"
        "\n\nCRITICAL: Output ONLY the JSON object. Do not include any text or markdown fences."
    )
    
    user_prompt = (
        f"The final itinerary to be confirmed is: {itinerary_text}. "
        f"The entire trip starts on the **actual date**: {start_date}. " 
        "Ensure your suggested booking times and confirmation codes are realistic considering this starting date."
    )

    try:
        # 3. Calling LLM to generate booking confirmations
        response = client.models.generate_content(
            model=os.environ.get("AGENT_MODEL"),
            contents=[system_prompt, user_prompt]
        )
        
        # 4. JSON
        raw_json_text = response.text.strip()
        raw_json_text = re.sub(r'```json|```', '', raw_json_text, flags=re.IGNORECASE).strip()
        data = json.loads(raw_json_text)
        
        # 5. Validation
        validated_confirmation = BookingConfirmation.model_validate(data)
        
        print(f"✅ The scheduling agent successfully confirmed {len(validated_confirmation.confirmation_list)} Simulated Booking.")
        
        successful_calls = 0
        
        for day_plan in final_itinerary:
            current_date = SchedulerTools.calculate_itinerary_date(start_date, day_plan.day) 
            print(f"Test: Day {day_plan.day} is {current_date}") # طباعة أفضل للاختبار
            # التكرار على جميع الأنشطة المخطط لها في هذا اليوم
            for activity_name in day_plan.activities:
                # Simulate sending the request
                success = SchedulerTools.send_to_booking_api(
                    activity=activity_name,
                    date=current_date
                )
                if success:
                    successful_calls += 1
        
        print(f"✅ Scheduling Agent: The booking tool has been successfully called. {successful_calls} مرات.")

        # =======================================================
        
        return validated_confirmation
        
    except Exception as e:
        print(f"❌ Scheduler failed to plan or verify JSON: {e}")
        return None       

# E: Search Agent To get destination Data
# Called From C: 1
def fetch_real_data_with_gemini_tool(destination: str, interests: list) -> str:
    """
    The Gemini model uses the built-in Google Search tool to retrieve real information.
    
    :param destination: The Area to be searched for on the web.
    :param interests: The interests in the Area to be searched for on the web.
    :returns: The model's response, which includes the search results.
    """
    
    interests_str = ", ".join(interests)
    
    # 1. Building the query
    query = (
        f"Key activities, estimated daily travel cost, and top tourist sites in {destination} "
        f"for a visitor interested in {interests_str}. Provide activity names and rough prices."
    )
    # 2. Drafting the claim
    prompt = (
        f"Use your access to Google Search to find the following information: {query}. "
        "Provide a concise summary including the average daily travel cost and two key historical activities."
    )
    
    try:
        # Call up
        response = client.models.generate_content(
            model=os.environ.get("AGENT_MODEL"),
            contents=[prompt],
            #config=config # تمرير التكوين
        )
        
        print("✅ Gemini successfully executed the search and generated a response.")
        return response.text
        
    except Exception as e:
        return f"❌ Failed to fetch data using Gemini tool: {e}"

# D: The Plan Agent
# Called From A: 3
def run_planner_agent(destination: str, duration: int, proposals: List[ActivityProposal], daily_budget: float) -> List[DailyPlan] | None:
    """
    The logistics planner agent organizes the selected activities into a coherent daily itinerary 
    that respects the total duration and the user's daily budget constraints.
    
    :param destination: The selected area for the travel (e.g., "Cairo").
    :param duration: The total number of days for the trip (e.g., 7).
    :param proposals: The list of analyzed and selected activity proposals (from the Investigator Agent).
    :param daily_budget: The maximum allowed spending per day (in USD, e.g., 180.0).
    :returns: The generated list of DailyPlan objects, or None if planning fails due to constraints.
    """
    if not client: return None

    # 1. Using the tool to collect logistical data (simulation)
    activity_names = [p.activity_name for p in proposals]
    logistics_data = TravelTools.calculate_travel_time(activity_names)
    
    # 2. Establishment of a list of activities and budget (as part of the context)
    proposals_text = json.dumps([p.model_dump() for p in proposals], ensure_ascii=False)

    # 3. Formulating the claim
    system_prompt = (
        "You are The Logistics Planner Agent, an expert in travel strategy. "
        f"Your goal is to organize the given activities into a cohesive, day-by-day itinerary for a {duration}-day trip (for simulation). "
        "Use the logistics data to group activities logically (e.g., geographically close). "
        "The total cost for any single day MUST NOT exceed the daily budget of $180. "
        "Your final output MUST be a JSON object with a key named 'itinerary' that strictly follows the provided Pydantic schema."
        f"\nSchema: {ItineraryList.model_json_schema()}"
        "\n\nCRITICAL: Output ONLY the JSON object. Do not include any text or markdown fences."
    )
    
    user_prompt = (
        f"Design the {duration}-day itinerary for {destination}. Daily Budget: ${daily_budget}. "
        f"Available Activities (with costs): {proposals_text}. "
        f"Logistical Constraints: {logistics_data}."
    )

    try:
        # Call LLM (without response_schema)
        response = client.models.generate_content(
            model=os.environ.get("AGENT_MODEL"),
            contents=[system_prompt, user_prompt]
        )
        
        raw_json_text = response.text.strip()
        raw_json_text = re.sub(r'```json|```', '', raw_json_text, flags=re.IGNORECASE).strip()

        data = json.loads(raw_json_text)
        
        # ⚠️ Reform step (packaging): If it generated a list instead of a dictionary
        if isinstance(data, list):
            fixed_data = {"itinerary": data}
        else:
            fixed_data = data
        
        validated_container = ItineraryList.model_validate(fixed_data)
        
        print("✅ The planning agent successfully generated the itinerary.!")
        return validated_container.itinerary
        
    except Exception as e:
        print(f"❌ The agent's failure to plan or verify JSON: {e}")
        return None        

# C: investigator Agent
# Called From A: 2
def run_investigator_agent(destination: str, interests: List[str]) -> List[ActivityProposal] | None:
    """
    The investigator agent conducts real-time web research (via Gemini Search Tool) to find 
    relevant activities and costs, then converts the findings into a structured list 
    of activity proposals in JSON format.
    
    :param destination: The confirmed travel destination (e.g., "Cairo, Egypt").
    :param interests: A list of the user's key interests (e.g., ["History", "Art", "Local Cuisine"]).
    :returns: A list of ActivityProposal objects containing the activity name, price, and description, 
              or None if the search fails or the JSON is invalid.
    """
    if not client:
        print("Agent execution skipped due to missing API client.")
        return None
    
    # Use the tool to collect the data the agent needs.
    tool_data = fetch_real_data_with_gemini_tool(destination, interests)
    if tool_data.startswith("❌ Failed"):
        print("Agent execution stopped due to failure in data fetching.")
        return None
    
    # صياغة المطالبة
    system_prompt = (
        "You are The Investigator Agent, an expert travel researcher. "
        "Your task is to analyze the provided travel data and user interests, "
        "then select exactly 5 highly relevant activities. "
        "Your output MUST be a clean JSON object containing a 'proposals' list that strictly follows the provided structure: "
        f"{ActivityProposalsList.model_json_schema()}"
        "\n\nCRITICAL: Output ONLY the JSON object. Do not include any explanations or markdown fences. "
        "ENSURE all elements in the array are separated by a COMMA. **IMPORTANT: 'estimated_cost' MUST be a number (float or integer), NOT a string (e.g., 25.0, not '25.0').**" # ⬅️ الإضافة الجديدة
        "DO NOT add any conversational text, explanations, or markdown fences (e.g., ```json) "
        "Generate a list of 5 activity proposals using the required JSON schema."
        "before or after the JSON output."
    )
    
    user_prompt = (
        f"Based on the following data: {tool_data}. "
        f"The user is planning a trip to {destination} with interests in {', '.join(interests)}. "
        
    )
    
    try:
        # LLM invocation with response JSON (Output Formatting)
        response = client.models.generate_content(
            model=os.environ.get("AGENT_MODEL"),
            contents=[system_prompt, user_prompt],
            
        )
        # Note: The Gemini API model returns JSON as text in response.text.
        raw_json_text = response.text.strip()
        
        # 🧹Additional cleaning step: Remove Markdown tags if they were added by mistake by the form.
        raw_json_text = re.sub(r'```json|```', '', raw_json_text, flags=re.IGNORECASE).strip()

        if not raw_json_text:
            raise ValueError("LLM returned an empty response text.")
        
        # Uploading raw text to the Python dictionary
        data = json.loads(raw_json_text)
        
        # ⚠️ The crucial step: fixing the structure before validating Pydantic
        if isinstance(data, list):
            # If the output is a list, wrap it inside the expected structure.
            fixed_data = {"proposals": data}
            print("🔧 Formatting fixed: Menu wrapped inside key 'proposals'.")
        elif isinstance(data, dict):
            # If the output is a dictionary, use it directly.
            fixed_data = data
        else:
             raise ValueError("LLM returned neither a list nor a dictionary.")
        
        # Validating the dictionary using the container Pydantic
        validated_container = ActivityProposalsList.model_validate(fixed_data)
        
        # Return to the actual list
        proposals = validated_container.proposals
        
        print("✅ The agent successfully generated valid and authenticated JSON (based on the claim).")
        return proposals
        
    except Exception as e:
        print(f"Error : B: ❌ Agent failed to generate or verify JSON: {e}")
        return None

# B Analyst Agent
# Called From A: 1
def run_memory_analyst_agent(duration_days: int, start_date: str, budget_range: str) -> List[DestinationProposal] | None:
    """
    The Memory Analyst Agent utilizes the LongTermMemoryTool to analyze the user's past travel 
    history and uses this context to suggest exactly 3 tailored destinations.
    
    :param duration_days: The requested number of days for the new trip.
    :param start_date: The actual start date of the planned trip (e.g., '2025-12-01').
    :param budget_range: The user's desired budget level (e.g., "Mid-range", "Luxury").
    :returns: A list of 3 structured DestinationProposal objects, including the estimated cost and reasoning, 
              or None if the agent fails to generate valid JSON.
    """
    if not client: return None

    # 1. Using the tool to retrieve the long-term memory report
    memory_report = LongTermMemoryTool.analyze_past_trips(budget_range, duration_days)
    
    # 2. Formulating the claim
    system_prompt = (
        "You are The Memory Analyst Agent. Your task is to propose exactly 3 destinations "
        "by analyzing the user's travel history and comparing it with their current budget and duration request. "
        "The output MUST be a clean JSON object with a key 'proposals' that strictly follows the provided schema. "
        f"\nSchema: {DestinationProposalsList.model_json_schema()}"
        "\n\nCRITICAL: Output ONLY the JSON object. Justify each proposal using data from the memory report."
    )
    
    user_prompt = (
        "Analyze the following data and generate 3 destination proposals: \n\n"
        f"*** USER REQUEST ***: The user requested a trip of {duration_days} days starts in {start_date} with a {budget_range} budget.\n\n"
        "*** MEMORY ANALYSIS REPORT START ***\n"
        f"{memory_report}\n" # ⬅️ وضع التقرير داخل فواصل
        "*** MEMORY ANALYSIS REPORT END ***\n\n"
        "Generate 3 destination proposals using the required JSON schema."
    )
    try:
        # Call LLM
        response = client.models.generate_content(
            model=os.environ.get("AGENT_MODEL"),
            contents=[system_prompt, user_prompt]
        )
        
        raw_json_text = response.text.strip()
        raw_json_text = re.sub(r'```json|```', '', raw_json_text, flags=re.IGNORECASE).strip()

        data = json.loads(raw_json_text)
        
        # ⚠️ Reform step (packaging)
        if isinstance(data, list):
            fixed_data = {"proposals": data}
        else:
            fixed_data = data
        
        validated_container = DestinationProposalsList.model_validate(fixed_data)
        
        print("✅ The analyst's assistant successfully analysed the memory and suggested destinations.")
        return validated_container.proposals
        
    except Exception as e:
        print(f"❌ Failure of the agent and memory: {e}")
        return None

# A: Start
def test_full_sequence_interactive(duration: int, start_date: str,interests: List[str], budget_range: str, daily_budget: float):
    """
    Executes the full multi-agent travel planning workflow interactively, simulating user selection.
    
    The sequence covers four main stages:
    1.  Memory Analysis: The Memory Analyst Agent proposes destinations based on past trips, 
        duration, and budget (using LongTermMemoryTool).
    2.  User Selection & Investigation: Simulates the user selecting a destination. The Investigator 
        Agent then searches for real activities and costs (using Gemini Search Tool).
    3.  Logistics Planning: The Planner Agent organizes the activities into a coherent daily itinerary, 
        respecting the duration and daily budget.
    4.  Execution Simulation: The Scheduler Agent simulates the final booking process, confirming 
        the activities and generating a confirmation summary.
        
    :param duration: Total duration of the trip in days.
    :param start_date: The actual start date of the trip ('YYYY-MM-DD').
    :param interests: A list of the user's key interests for the trip.
    :param budget_range: The general budget level (e.g., "Mid-range").
    :param daily_budget: The maximum spending limit per day (float).
    :returns: None (This function primarily prints the process and the final output to the console).
    """
    # ----------------------------------------------------
    # Stage 0: Memory Analyst Agent
    # ----------------------------------------------------
    print("--- 0. Run the memory agent and analyser to suggest destinations. ---")
    suggested_destinations = run_memory_analyst_agent(duration, start_date, budget_range)
    
    if not suggested_destinations:
        print("❌ Sequence failure: The memory agent did not provide any suggestions.")
        return

    print("\n--- ✅ Destinations suggested based on previous history ---")
    
    # User selection simulation
    selected_proposal = suggested_destinations[0] # ⬅️ We choose the first suggestion as an example.
    
    # Specifying the data that would be collected interactively via conversation
    final_destination = selected_proposal.destination_name
    
    print(f"--- 🗣️ Simulating user decision: Selected {final_destination} With interest {interests} ---")
    
    # ----------------------------------------------------
    # Stage 1: Investigator Agent
    # ----------------------------------------------------
    print("\n--- 1. Run the Investigator Agent to fetch real activities (using Google Search Tool) ---")
    proposals = run_investigator_agent(final_destination, interests)

    if proposals:
        # ----------------------------------------------------
        # Stage 2: Logistics Planner Agent (Planner Agent)
        # ----------------------------------------------------
        print("\n--- 2. Run the logistics planner agent to create the route. ---")
        itinerary = run_planner_agent(final_destination, duration, proposals, daily_budget)
        
        if itinerary:
            print("\n--- 🗺️ The final track has been successfully created. ---")
            
            for day_plan in itinerary:
                print(f"Day {day_plan.day} ({day_plan.theme}): {', '.join(day_plan.activities)} | Cost: ${day_plan.total_daily_cost}")
                
            # =======================================================
            # ⬅️ Required modification: Add a call to the scheduling agent. (Scheduler Agent)
            # =======================================================
            
            print("\n--- 3. Run the Scheduling and Booking Agent (Simulated Booking) ---")
            confirmation = run_scheduler_agent(itinerary,start_date) # ⬅️ The new call
            
            if confirmation:
                print("\n--- 🏁 Sequence complete: Simulated reservations confirmed ---")
                print(f"✅ Total confirmed cost of bookings: ${confirmation.total_cost_booked:.2f}")
                print(f"✅ Confirmed {len(confirmation.confirmation_list)} Reservation. (Example: {confirmation.confirmation_list[0].activity_name})")
            else:
                print("❌ Sequence failure: The scheduling agent did not succeed.")
            
        else:
            print("❌ Sequence failure: The agent didn't work..")
    else:
        print("❌ Sequence failure: The agent didn't work..")


# Load API Key
try:
    load_dotenv()
    os.environ["GOOGLE_API_KEY"] = os.environ.get("GOOGLE_API_KEY") 
    print("✅ Gemini API key setup complete.")
except Exception as e:
    print(
        f"🔑 Authentication Error: Please make sure you have added 'GOOGLE_API_KEY' to your Kaggle secrets. Details: {e}"
    )

# Ensure that the environment variable for the API key is defined.
try:
    client = genai.Client()
except Exception:
    print("⚠️ WARNING: Google GenAI Client not initialized. Check your API Key.")
    client = None

if __name__ == "__main__":
    
    test_full_sequence_interactive(duration=4,start_date='2025-12-01',interests=["History", "Food"], budget_range="Mid-range", daily_budget=180.0)
