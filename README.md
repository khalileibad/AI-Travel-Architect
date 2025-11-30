# AI Travel Architect
Personalized Trip Planning & Scheduling System

# 🤖 AI Travel Planning Agents

**Intelligent, Multi-Agent System for Personalized and Context-Aware Travel Itinerary Planning.**

This project demonstrates a robust, sequential architecture of specialized AI agents built using the Google Gemini API. The system transforms high-level user requests and historical data into a finalized, executable, and budget-constrained travel itinerary.



## ✨ Features

* **Memory-Driven Proposals:** Analyzes past trip data to suggest relevant destinations.
* **Real-Time Grounding:** Uses the **Gemini Search Tool** to fetch live activity costs and details.
* **Logistics Optimization:** Planner Agent respects strict **daily budget** and trip duration constraints.
* **Structured Output:** All agents communicate using validated **Pydantic/JSON** schemas, ensuring a clean data pipeline.
* **Simulated Execution:** The Scheduler Agent simulates the final booking process with calculated dates.

## ⚙️ Architecture: The 4-Stage Pipeline

The system is built as a sequential chain of specialized agents:

| Agent | Core Function | Key Tool/Strategy | Output |
| :--- | :--- | :--- | :--- |
| **1. Memory Analyst** | Propose 3 destinations based on past preferences and new budget/duration. | `LongTermMemoryTool` | `DestinationProposalsList` |
| **2. Investigator** | Research real activities, costs, and details related to the selected destination and interests. | **Gemini Search Tool** | `ActivityProposalsList` (Structured activities with prices) |
| **3. Logistics Planner** | Organize activities day-by-day, optimizing the route and adhering to the `daily_budget`. | Constraint-based Reasoning | `ItineraryList` (DailyPlan) |
| **4. Scheduler/Booking** | Simulate final reservation and booking confirmation. | `SchedulerTools` (Simulated Booking) | `BookingConfirmation` |

## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### 1. Prerequisites

* Python 3.10+
* A Google AI API Key (Get it from Google AI Studio).

### 2. Clone the Repository

```bash
git clone [YOUR_REPOSITORY_URL]
cd [YOUR_PROJECT_FOLDER]
