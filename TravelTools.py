# Process simulation tools For Capstone
from schemas import DailyPlan, ActivityProposal
from typing import Dict, Any, List
from datetime import datetime, timedelta

class TravelTools:
    """Contains simulation tools used by agents"""

    @staticmethod
    def calculate_travel_time(activities_list: List[str]) -> str:
        """(Maps/Distance Tool) تحاكي حساب وقت التنقل بين نقاط الاهتمام."""
        print(f"--- TOOL USE: Calculating travel logistics for {len(activities_list)} points ---")
        # Simulation for calculating distances to estimate travel time
        return "Logistics Report: 4 activities/day is optimal to keep travel time under 1.5 hours total. Keep Louvre and Orsay together. Eiffel Tower requires half a day."

    @staticmethod
    def calendar_scheduler(plan: List[DailyPlan]) -> str:
        """(Calendar Tool) تحاكي جدولة المسار في تقويم خارجي."""
        print(f"--- TOOL USE: Scheduling {len(plan)} days in Calendar ---")
        # محاكاة نتيجة الجدولة
        return f"SUCCESS: The 7-day itinerary has been successfully added to the user's calendar starting on {plan[0].date}. Booking links (simulated) have been attached."
        
    
    @staticmethod
    def calculate_travel_time(activities_list: List[str]) -> str:
        """(Maps/Distance Tool Simulation) Simulates travel time between points of interest."""
        print(f"--- TOOL USE: Calculating travel logistics for {len(activities_list)} activities ---")
        # Provides logical data needed by the agent to arrange activities
        return (
            "Logistics Report: The Pyramids require a full morning. "
            "The Egyptian Museum and Khan el-Khalili are geographically close and can be grouped into one day. "
            "The Citadel is best visited on a separate day due to traffic."
        )

class LongTermMemoryTool:
    """
    أداة محاكاة لقاعدة بيانات الذاكرة طويلة الأمد (Long-Term Memory / RAG)
    لتحليل رحلات المستخدم السابقة.
    """

    @staticmethod
    def _mock_user_history() -> List[Dict[str, Any]]:
        """قاعدة بيانات وهمية لسجلات الرحلات السابقة للمستخدم."""
        return [
            {"trip_id": 1, "destination": "Japan (Tokyo)", "duration": 10, "budget_spent": 3500, "interests": ["Culture", "Food"], "season": "Spring"},
            {"trip_id": 2, "destination": "Italy (Rome)", "duration": 5, "budget_spent": 1200, "interests": ["History", "Art"], "season": "Autumn"},
            {"trip_id": 3, "destination": "UAE (Dubai)", "duration": 4, "budget_spent": 1800, "interests": ["Shopping", "Luxury"], "season": "Winter"},
        ]

    @staticmethod
    def analyze_past_trips(budget_range: str, duration_days: int) -> str:
        """
        تقوم بتحليل السجلات السابقة وتقديم تقرير للمقارنة والاقتراح.

        :param budget_range: الميزانية المطلوبة من المستخدم (مثلاً: "متوسطة" أو "عالية").
        :param duration_days: المدة المطلوبة للرحلة.
        :returns: تقرير نصي يعتمد عليه الوكيل للاقتراح.
        """
        history = LongTermMemoryTool._mock_user_history()
        
        # 1. حساب المتوسطات والتفضيلات
        total_spent = sum(t['budget_spent'] for t in history)
        avg_spent = total_spent / len(history) if history else 0
        
        # 2. تحديد الاهتمام الأكثر تكراراً
        all_interests = [i for trip in history for i in trip['interests']]
        most_common_interest = max(set(all_interests), key=all_interests.count) if all_interests else "N/A"

        # 3. صياغة تقرير الذاكرة
        report = (
            f"--- MEMORY ANALYSIS REPORT ---\n"
            f"User History: {len(history)} past trips recorded.\n"
            f"Average total trip cost: ${avg_spent:.2f}. Past budgets suggest a preference for trips between $1200 and $3500.\n"
            f"Most preferred interests: {most_common_interest} (e.g., Culture, Food).\n"
            f"Past seasons chosen: Spring, Autumn, Winter.\n\n"
            f"Proposed Destinations (based on past success and new budget/duration of {duration_days} days):\n"
            f"1. **Thailand (Bangkok):** Suitable for a {budget_range} budget, strong Food and Culture interests, similar to Japan but lower cost. Estimated cost: $1500.\n"
            f"2. **Portugal (Lisbon):** Strong History/Culture interest, similar to Italy but offers new scenery. Estimated cost: $1000.\n"
            f"3. **South Korea (Seoul):** New Culture experience, good for {duration_days} days. Estimated cost: $2200."
        )
        print("--- 🌐 TOOL USE: Executing LongTermMemoryTool ---")
        return report

class SchedulerTools:
    """
    Tools for simulating interaction with an external scheduling and booking system.
    """
    
    @staticmethod
    def send_to_booking_api(activity: str, date: str) -> bool:
        """
        Simulate the process of sending a final booking request to an external API.
        
        :param activity: Name of activity/reservation.
        :param date: Date of booking.
        :returns: True If the booking is ‘successful’ (in the simulation).
        """
        # في مشروع حقيقي، سيتم هنا استدعاء requests.post('booking_service/api/...')
        print(f"--- 📞 TOOL USE: Sending simulated booking request for {activity} on {date} ---")
        return True

    def calculate_itinerary_date(start_date_str: str, day_number: int) -> str:
        """
        Calculate the actual date for a given day in the track.
        
        :param start_date_str: Start date in format 'YYYY-MM-DD'.
        :param day_number: Day's number on the track (1-indexed).
        :returns: The actual date of that day in the format 'YYYY-MM-DD'.
        """
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            
            target_date = start_date + timedelta(days=day_number - 1)
            
            return target_date.strftime('%Y-%m-%d')
        except ValueError:
            print("⚠️ Error in start date format. Must be 'YYYY-MM-DD'.")
            return "N/A"