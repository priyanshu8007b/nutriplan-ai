# 🥗 NutriPlan AI

> Personalized meal planning powered by BMR-based nutrition science and constraint optimization.

NutriPlan AI generates customized weekly meal plans by calculating each user's actual calorie and protein needs from body stats, then optimizing meal selection across multiple constraints (budget, allergens, preferences, variety) with built-in nutritional guardrails.

---

## ✨ Features

- **BMR-Driven Targets** — Calculates calorie needs using the Mifflin-St Jeor formula, adjusted by activity level
- **Personalized Protein Goals** — Daily protein computed from body weight × goal intensity (0.8 / 1.4 / 2.0 g/kg)
- **Multi-Factor Meal Scoring** — Each candidate meal scored on protein fit, calorie match, preference alignment, and budget
- **Hard Allergen Guardrails** — Zero-tolerance exclusion for user-specified allergens
- **Soft Constraint Validation** — Flags days where calories, budget, or protein deviate from targets
- **Variety Enforcement** — Prevents meal repetition within a 15-meal sliding window
- **Realistic 5-Meal Days** — Breakfast, morning snack, lunch, evening snack, dinner
- **Auto-Generated Explanations** — Each meal includes a template-based reason for selection

---

## 🏗 Architecture

```
React UI
   │ POST /generate-plan
   ▼
FastAPI Backend
   │
   ├── BMR/TDEE Calculator    → calorie & protein targets
   ├── Filter Engine          → allergens (hard) + prefs
   ├── Scoring Engine         → multi-factor meal ranking
   ├── Plan Builder           → 5 meals × N days
   └── Validator              → guardrail flags
   │
   ▼
SQLite (310 recipes)
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (functional components, hooks) |
| Backend | FastAPI + Pydantic |
| Database | SQLite (310 curated recipes) |
| Validation | Pydantic models with Field constraints |
| Styling | Vanilla CSS |

---

## 🧪 Nutrition Science

### BMR — Mifflin-St Jeor Formula

```
Male:    BMR = 10 × weight + 6.25 × height − 5 × age + 5
Female:  BMR = 10 × weight + 6.25 × height − 5 × age − 161
```

### TDEE — Activity Multipliers

| Level | Multiplier |
|---|---|
| Sedentary (desk job) | 1.2 |
| Light (1–3 workouts/week) | 1.375 |
| Moderate (3–5 workouts/week) | 1.55 |
| Active (6–7 workouts/week) | 1.725 |
| Very Active (athlete) | 1.9 |

### Protein per kg body weight

| Goal | g/kg |
|---|---|
| Low (sedentary baseline) | 0.8 |
| Medium (general fitness) | 1.4 |
| High (muscle building) | 2.0 |

---

## 🛡 Guardrails

| Type | Rule | Behavior |
|---|---|---|
| Allergen | Recipe contains user allergen | Hard exclude |
| Budget | Day cost > daily budget | Flag |
| Calorie | Day cal < 85% or > 115% of target | Flag |
| Protein | Day protein < 85% of target | Flag |
| Variety | < 50% unique meals in plan | Flag |
| Filter | < 9 recipes after filtering | Reject with helpful error |

---

## 🚀 Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
python database.py
uvicorn main:app --reload
```

Runs on `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm start
```

Runs on `http://localhost:3000`

Open `http://localhost:8000/docs` to explore the interactive API.

---

## 📡 API Reference

### `POST /generate-plan`

**Request:**

```json
{
  "age": 22,
  "gender": "male",
  "height_cm": 175,
  "weight_kg": 70,
  "activity_level": "moderate",
  "preferences": ["veg", "high-protein"],
  "allergens": ["dairy"],
  "budget_per_day": 250,
  "days": 7,
  "protein_level": "high"
}
```

**Response:** Full weekly plan with nutrition profile, day-by-day meals, guardrail flags, and grocery list.

---

## 📁 Project Structure

```
nutriplan-ai/
├── backend/
│   ├── database.py        # SQLite schema + 310 seeded recipes
│   ├── models.py          # Pydantic request/response models
│   ├── engine.py          # BMR calc + filter + scoring + validation
│   ├── main.py            # FastAPI app + endpoints
│   ├── requirements.txt
│   └── nutriplan.db       # auto-generated
├── frontend/
│   ├── public/
│   └── src/
│       ├── App.js
│       ├── App.css
│       └── index.js
└── README.md
```

---

## 🔮 Future Improvements

- LLM-powered meal explanations (OpenAI / local Llama)
- Macro split with carb and fat targets
- Plan history with user accounts
- Grocery list with actual ingredient aggregation
- Mobile-responsive layout
- Export plan as PDF

---

## 👤 Author

**Priyanshu** — MTech Student  
Built as a demonstration of full-stack engineering, applied nutrition science, and constraint-based AI planning.