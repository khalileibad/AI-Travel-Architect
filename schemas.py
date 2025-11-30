from pydantic import BaseModel, Field
from typing import List
# Model for data reception between agents

class ActivityProposal(BaseModel):
    activity_name: str = Field(description="Short name of activity.")
    estimated_cost: float = Field(description="Approximate cost of activity (in dollars).")
    category: str = Field(description="Activity category (e.g., “Art”, “Food”, “History”).")

class DailyPlan(BaseModel):
    day: int = Field(description="Day's number on the journey.")
    date: str = Field(description="Actual date for Day (simulation).")
    theme: str = Field(description="Day's main topic (e.g., “art tour”).")
    activities: List[str] = Field(description="List of activities scheduled for Day.")
    total_daily_cost: float = Field(description="Total estimated cost for Day.")

class ItineraryList(BaseModel):
    itinerary: List[DailyPlan] = Field(description="A list of DailyPlan objects representing the full itinerary.")

class ActivityProposalsList(BaseModel):
    proposals: List[ActivityProposal] = Field(description="A list of 5 generated activity proposals.")

class DestinationProposal(BaseModel):
    """Travel destination suggestion form."""
    destination_name: str = Field(description="Proposed name of destination (city and country).")
    reasoning: str = Field(description="Summary of the reason for the suggestion, related to user preferences or budget.")
    estimated_total_cost: float = Field(description="The estimated total cost of the proposed trip.")

class DestinationProposalsList(BaseModel):
    """The container for the list of destination suggestions."""
    proposals: List[DestinationProposal] = Field(description="A list of three destination suggestions based on memory analysis.")
    
class ConfirmationDetails(BaseModel):
    activity_name: str = Field(description="Name of booked activity or hotel")
    status: str = Field(description="Booking status: 'Confirmed' or 'Pending'.")
    confirmation_code: str = Field(description="confirmation code for booking.")
    booking_time: str = Field(description="The specified time (e.g., 09:00 AM).")

class BookingConfirmation(BaseModel):
    total_cost_booked: float = Field(description="The total confirmed cost of reservations.")
    confirmation_list: List[ConfirmationDetails] = Field(description="A list of all activities and hotels that have been confirmed.")

