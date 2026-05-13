from pydantic import BaseModel, Field
from typing import List

# What the user sends us
class PlanRequest(BaseModel):
    # User stats
    age: int = Field(default=25, ge=10, le=100)
    gender: str = Field(default="male")  # "male" or "female"
    height_cm: float = Field(default=170, ge=100, le=250)
    weight_kg: float = Field(default=70, ge=30, le=200)
    activity_level: str = Field(default="moderate")
    # sedentary, light, moderate, active, very_active

    # Diet preferences
    preferences: List[str] = []
    allergens: List[str] = []
    budget_per_day: int = Field(default=200, ge=50, le=500)
    days: int = Field(default=7, ge=1, le=14)
    protein_level: str = Field(default="medium")  # low, medium, high

# One meal
class Meal(BaseModel):
    name: str
    category: str
    calories: int
    protein: int
    cost: int
    reason: str

# One full day
class DayPlan(BaseModel):
    day_number: int
    breakfast: Meal
    snack1: Meal
    lunch: Meal
    snack2: Meal
    dinner: Meal
    day_calories: int
    day_cost: int
    day_protein: int
    flags: List[str]

# User's calculated nutrition profile
class NutritionProfile(BaseModel):
    bmr: int                     # base metabolic rate
    tdee: int                    # total daily energy expenditure
    calorie_target: int          # what we plan for
    protein_target: int          # daily protein goal (grams)
    explanation: str             # short message for user

# Full plan response
class WeeklyPlan(BaseModel):
    profile: NutritionProfile
    days: List[DayPlan]
    total_cost: int
    total_calories: int
    avg_protein: int
    grocery_list: dict
    guardrail_flags: List[str]