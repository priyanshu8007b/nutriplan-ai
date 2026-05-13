import sqlite3
from typing import List, Dict
from models import Meal, DayPlan, WeeklyPlan

# ─────────────────────────────────────────────
# NUTRITION CALCULATOR (BMR + TDEE + Protein)
# ─────────────────────────────────────────────

ACTIVITY_MULTIPLIERS = {
    'sedentary':   1.2,
    'light':       1.375,
    'moderate':    1.55,
    'active':      1.725,
    'very_active': 1.9,
}

PROTEIN_PER_KG = {
    'low':    0.8,   # sedentary baseline
    'medium': 1.4,   # general fitness
    'high':   2.0,   # muscle building / athlete
}

def calculate_bmr(age: int, gender: str, height_cm: float, weight_kg: float) -> int:
    """
    Mifflin-St Jeor formula — most accurate BMR estimator.
    Returns calories burned at rest per day.
    """
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    if gender.lower() == 'male':
        bmr = base + 5
    else:
        bmr = base - 161
    return int(bmr)


def calculate_tdee(bmr: int, activity_level: str) -> int:
    """
    Total Daily Energy Expenditure = BMR × activity multiplier.
    """
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)
    return int(bmr * multiplier)


def calculate_protein_target(weight_kg: float, protein_level: str) -> int:
    """
    Protein in grams = body weight × g/kg ratio.
    """
    ratio = PROTEIN_PER_KG.get(protein_level, 1.4)
    return int(weight_kg * ratio)


def build_nutrition_profile(
    age: int,
    gender: str,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    protein_level: str
):
    """
    Returns dict with bmr, tdee, calorie_target, protein_target, explanation.
    """
    bmr = calculate_bmr(age, gender, height_cm, weight_kg)
    tdee = calculate_tdee(bmr, activity_level)
    protein_target = calculate_protein_target(weight_kg, protein_level)

    explanation = (
        f"Based on your stats: BMR is {bmr} cal/day, "
        f"and with {activity_level.replace('_', ' ')} activity your TDEE is {tdee} cal/day. "
        f"Protein target: {protein_target}g/day ({PROTEIN_PER_KG[protein_level]}g per kg of body weight)."
    )

    return {
        'bmr': bmr,
        'tdee': tdee,
        'calorie_target': tdee,
        'protein_target': protein_target,
        'explanation': explanation
    }

# ─────────────────────────────────────────────
# DATABASE HELPER
# ─────────────────────────────────────────────

def fetch_all_recipes() -> List[Dict]:
    conn = sqlite3.connect('nutriplan.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM recipes')
    rows = c.fetchall()
    conn.close()

    recipes = []
    for r in rows:
        recipes.append({
            'id':          r['id'],
            'name':        r['name'],
            'category':    r['category'],
            'calories':    r['calories'],
            'protein':     r['protein'],
            'cost':        r['cost'],
            'tags':        r['tags'].split(',') if r['tags'] else [],
            'allergens':   r['allergens'].split(',') if r['allergens'] else [],
            'ingredients': r['ingredients']
        })
    return recipes


# ─────────────────────────────────────────────
# NODE 1: FILTER
# ─────────────────────────────────────────────

def filter_recipes(
    all_recipes: List[Dict],
    preferences: List[str],
    allergens: List[str]
) -> List[Dict]:
    filtered = []

    for recipe in all_recipes:
        # HARD BLOCK: allergen check
        user_allergens = [a.strip() for a in allergens if a.strip()]
        recipe_allergens = recipe['allergens']
        if any(a in recipe_allergens for a in user_allergens):
            continue

        # SOFT BLOCK: preference check
        if preferences:
            user_prefs = [p.strip() for p in preferences if p.strip()]
            recipe_tags = recipe['tags']
            if not any(p in recipe_tags for p in user_prefs):
                continue

        filtered.append(recipe)

    return filtered


# ─────────────────────────────────────────────
# NODE 2: SCORE & PICK MEAL
# ─────────────────────────────────────────────

def score_meal(
    meal: Dict,
    cal_target: int,
    cost_limit: int,
    user_prefs: List[str],
    protein_floor: int
) -> float:
    """
    Score a meal 0-100. Higher = better.
    protein_floor: minimum protein required for this meal.
    """
    score = 0

    # ─── 1. PROTEIN (40 points) ───
    if meal['protein'] < protein_floor:
        protein_score = (meal['protein'] / protein_floor) * 20
    else:
        protein_score = 20 + min((meal['protein'] - protein_floor) / protein_floor, 1.0) * 20
    score += protein_score

    # ─── 2. CALORIE FIT (30 points) ───
    cal_diff = abs(meal['calories'] - cal_target)
    cal_score = max(0, 1 - (cal_diff / 250)) * 30
    score += cal_score

    # ─── 3. PREFERENCE MATCH (20 points) ───
    if user_prefs:
        matches = sum(1 for p in user_prefs if p in meal['tags'])
        score += (matches / len(user_prefs)) * 20
    else:
        score += 10

    # ─── 4. BUDGET (10 points) ───
    if meal['cost'] <= cost_limit:
        score += 10
    else:
        over = meal['cost'] - cost_limit
        score += max(0, 10 - (over / 5))

    return score


def pick_meal(
    pool: List[Dict],
    category: str,
    cal_limit: int,
    cost_limit: int,
    recently_used: List[str],
    user_prefs: List[str],
    protein_floor: int
) -> Dict:
    category_pool = [m for m in pool if m['category'] == category]
    if not category_pool:
        raise ValueError(f"No recipes for category: {category}")

    fresh = [m for m in category_pool if m['name'] not in recently_used]
    candidates = fresh if fresh else category_pool

    scored = [(m, score_meal(m, cal_limit, cost_limit, user_prefs, protein_floor)) for m in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]


# ─────────────────────────────────────────────
# NODE 3: EXPLAIN
# ─────────────────────────────────────────────

def generate_reason(meal: Dict, user_prefs: List[str]) -> str:
    tags = meal['tags']
    name = meal['name']
    protein = meal['protein']
    calories = meal['calories']
    cost = meal['cost']

    if 'high-protein' in tags and 'high-protein' in user_prefs:
        return f"{name} gives {protein}g protein — great for your high-protein goal."
    if 'low-carb' in tags and 'low-carb' in user_prefs:
        return f"{name} is low-carb at {calories} cal — keeps blood sugar stable."
    if 'keto' in tags and 'keto' in user_prefs:
        return f"{name} fits keto — high fat, minimal carbs."
    if 'vegan' in tags:
        return f"{name} is plant-based — fiber rich at {calories} cal."
    if 'gf' in tags:
        return f"{name} is gluten-free — easy on digestion."
    if cost <= 50:
        return f"{name} is budget friendly at Rs.{cost} — great value."
    if protein >= 20:
        return f"{name} packs {protein}g protein — keeps you full longer."

    return f"{name} — balanced at {calories} cal and Rs.{cost}. Fits your targets."


# ─────────────────────────────────────────────
# NODE 4: BUILD PLAN
# ─────────────────────────────────────────────
def build_plan(
    filtered_recipes: List[Dict],
    calorie_target: int,
    budget_per_day: int,
    days: int,
    preferences: List[str],
    protein_target: int
) -> List[DayPlan]:
    """
    Build day plan with 5 slots.
    Uses actual protein_target (grams/day) calculated from BMR.
    """
    day_plans = []
    recently_used = []

    # Calorie split
    cal = {
        'breakfast': int(calorie_target * 0.22),
        'snack1':    int(calorie_target * 0.08),
        'lunch':     int(calorie_target * 0.32),
        'snack2':    int(calorie_target * 0.08),
        'dinner':    int(calorie_target * 0.30),
    }
    cost = {
        'breakfast': int(budget_per_day * 0.20),
        'snack1':    int(budget_per_day * 0.10),
        'lunch':     int(budget_per_day * 0.30),
        'snack2':    int(budget_per_day * 0.10),
        'dinner':    int(budget_per_day * 0.30),
    }

    # Protein floor per meal
    # Mains carry ~25% each, snacks ~12.5% each (4 mains-equivalent)
    main_floor  = int(protein_target * 0.25)
    snack_floor = int(protein_target * 0.12)

    for day_num in range(1, days + 1):
        breakfast = pick_meal(filtered_recipes, 'breakfast', cal['breakfast'], cost['breakfast'], recently_used, preferences, main_floor)
        snack1    = pick_meal(filtered_recipes, 'snack',     cal['snack1'],    cost['snack1'],    recently_used, preferences, snack_floor)
        lunch     = pick_meal(filtered_recipes, 'lunch',     cal['lunch'],     cost['lunch'],     recently_used, preferences, main_floor)
        snack2    = pick_meal(filtered_recipes, 'snack',     cal['snack2'],    cost['snack2'],    recently_used, preferences, snack_floor)
        dinner    = pick_meal(filtered_recipes, 'dinner',    cal['dinner'],    cost['dinner'],    recently_used, preferences, main_floor)

        meals = [breakfast, snack1, lunch, snack2, dinner]
        day_cal  = sum(m['calories'] for m in meals)
        day_cost = sum(m['cost']     for m in meals)
        day_prot = sum(m['protein']  for m in meals)

        flags = []
        if day_cost > budget_per_day:
            flags.append(f"Cost Rs.{day_cost} exceeds budget Rs.{budget_per_day}.")
        if day_cal < calorie_target * 0.85:
            flags.append(f"Calories {day_cal} below 85% of target {calorie_target}.")
        if day_cal > calorie_target * 1.15:
            flags.append(f"Calories {day_cal} above 115% of target {calorie_target}.")
        if day_prot < protein_target * 0.85:
            flags.append(f"Protein {day_prot}g below 85% of target {protein_target}g.")

        def to_meal(m, cat):
            return Meal(
                name=m['name'], category=cat,
                calories=m['calories'], protein=int(m['protein']),
                cost=m['cost'], reason=generate_reason(m, preferences)
            )

        day_plans.append(DayPlan(
            day_number=day_num,
            breakfast=to_meal(breakfast, 'breakfast'),
            snack1=to_meal(snack1, 'morning snack'),
            lunch=to_meal(lunch, 'lunch'),
            snack2=to_meal(snack2, 'evening snack'),
            dinner=to_meal(dinner, 'dinner'),
            day_calories=day_cal,
            day_cost=day_cost,
            day_protein=day_prot,
            flags=flags
        ))

        recently_used.extend([m['name'] for m in meals])
        if len(recently_used) > 15:
            recently_used = recently_used[-15:]

    return day_plans


# ─────────────────────────────────────────────
# NODE 5: VALIDATE
# ─────────────────────────────────────────────

def validate_plan(
    day_plans: List[DayPlan],
    calorie_target: int,
    budget_per_day: int
) -> List[str]:
    warnings = []
    n = len(day_plans)

    # 1. Protein check
    avg_protein = sum(d.day_protein for d in day_plans) / n
    if avg_protein < 50:
        warnings.append(
            f"Low protein: avg {avg_protein:.0f}g/day. Add eggs, paneer, or chicken."
        )

    # 2. Budget check
    over_budget_days = sum(1 for d in day_plans if d.day_cost > budget_per_day)
    if over_budget_days >= 3:
        warnings.append(
            f"{over_budget_days}/{n} days exceeded budget. Relax preferences or increase budget."
        )

    # 3. Calorie check
    avg_cal = sum(d.day_calories for d in day_plans) / n
    if avg_cal < calorie_target * 0.85:
        warnings.append(
            f"Average calories {avg_cal:.0f} is below 85% of target {calorie_target}."
        )

    # 4. Variety check (across all 5 meals now)
    all_meal_names = []
    for d in day_plans:
        all_meal_names.extend([d.breakfast.name, d.snack1.name, d.lunch.name, d.snack2.name, d.dinner.name])

    unique_meals  = len(set(all_meal_names))
    total_meals   = len(all_meal_names)
    variety_ratio = unique_meals / total_meals

    if variety_ratio < 0.5:
        warnings.append(
            f"Low variety: only {unique_meals} unique meals across {total_meals} total."
        )

    return warnings


# ─────────────────────────────────────────────
# GROCERY LIST
# ─────────────────────────────────────────────

def build_grocery_list(day_plans: List[DayPlan]) -> Dict[str, int]:
    meal_count = {}
    for day in day_plans:
        for meal in [day.breakfast, day.snack1, day.lunch, day.snack2, day.dinner]:
            meal_count[meal.name] = meal_count.get(meal.name, 0) + 1
    return meal_count