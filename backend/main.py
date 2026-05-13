from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import PlanRequest, WeeklyPlan, NutritionProfile
from database import init_db, get_db_connection
from engine import (
    fetch_all_recipes,
    filter_recipes,
    build_plan,
    validate_plan,
    build_grocery_list,
    build_nutrition_profile
)

app = FastAPI(
    title="NutriPlan AI",
    description="BMR-based meal planning with nutritional guardrails",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    print("NutriPlan AI is running.")

@app.get("/")
def root():
    return {"status": "ok", "message": "NutriPlan AI is live."}

@app.get("/recipes")
def get_recipes():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, category, calories, protein, cost, tags FROM recipes')
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id":       r["id"],
            "name":     r["name"],
            "category": r["category"],
            "calories": r["calories"],
            "protein":  r["protein"],
            "cost":     r["cost"],
            "tags":     r["tags"]
        }
        for r in rows
    ]

@app.post("/generate-plan", response_model=WeeklyPlan)
def generate_plan(req: PlanRequest):
    # Step 1: Build nutrition profile from BMR
    profile = build_nutrition_profile(
        req.age, req.gender, req.height_cm, req.weight_kg,
        req.activity_level, req.protein_level
    )

    # Step 2: Get all recipes
    all_recipes = fetch_all_recipes()

    # Step 3: Filter by preferences + allergens
    filtered = filter_recipes(all_recipes, req.preferences, req.allergens)

    if len(filtered) < 9:
        raise HTTPException(
            status_code=400,
            detail=f"Only {len(filtered)} recipes match your filters. Relax preferences or remove allergens."
        )

    # Step 4: Build plan using calculated targets
    try:
        day_plans = build_plan(
            filtered,
            profile['calorie_target'],
            req.budget_per_day,
            req.days,
            req.preferences,
            profile['protein_target']
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 5: Validate
    guardrail_flags = validate_plan(day_plans, profile['calorie_target'], req.budget_per_day)

    # Step 6: Aggregate
    total_cost     = sum(d.day_cost for d in day_plans)
    total_calories = sum(d.day_calories for d in day_plans)
    avg_protein    = int(sum(d.day_protein for d in day_plans) / len(day_plans))
    grocery        = build_grocery_list(day_plans)

    return WeeklyPlan(
        profile=NutritionProfile(**profile),
        days=day_plans,
        total_cost=total_cost,
        total_calories=total_calories,
        avg_protein=avg_protein,
        grocery_list=grocery,
        guardrail_flags=guardrail_flags
    )