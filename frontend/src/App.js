import { useState } from 'react';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  // ─── User stats ───
  const [age, setAge] = useState(22);
  const [gender, setGender] = useState('male');
  const [height, setHeight] = useState(175);
  const [weight, setWeight] = useState(70);
  const [activityLevel, setActivityLevel] = useState('moderate');

  // ─── Diet inputs ───
  const [preferences, setPreferences] = useState([]);
  const [allergens, setAllergens] = useState([]);
  const [budget, setBudget] = useState(200);
  const [days, setDays] = useState(3);
  const [proteinLevel, setProteinLevel] = useState('medium');

  // ─── API state ───
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const prefOptions = [
    { value: 'veg', label: 'Vegetarian' },
    { value: 'vegan', label: 'Vegan' },
    { value: 'gf', label: 'Gluten-Free' },
    { value: 'high-protein', label: 'High Protein' },
    { value: 'low-carb', label: 'Low Carb' },
    { value: 'non-veg', label: 'Non-Vegetarian' },
  ];

  const allergenOptions = [
    { value: 'dairy', label: 'Dairy' },
    { value: 'gluten', label: 'Gluten' },
    { value: 'nuts', label: 'Nuts' },
    { value: 'soy', label: 'Soy' },
    { value: 'eggs', label: 'Eggs' },
  ];

  const proteinOptions = [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
  ];

  const activityOptions = [
    { value: 'sedentary', label: 'Sedentary (desk job)' },
    { value: 'light', label: 'Light (1-3 workouts/week)' },
    { value: 'moderate', label: 'Moderate (3-5 workouts/week)' },
    { value: 'active', label: 'Active (6-7 workouts/week)' },
    { value: 'very_active', label: 'Very Active (athlete)' },
  ];

  const toggle = (list, setList, value) => {
    if (list.includes(value)) setList(list.filter(x => x !== value));
    else setList([...list, value]);
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    setPlan(null);

    try {
      const response = await fetch(`${API_URL}/generate-plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          age,
          gender,
          height_cm: height,
          weight_kg: weight,
          activity_level: activityLevel,
          preferences,
          allergens,
          budget_per_day: budget,
          days,
          protein_level: proteinLevel
        })
      });

      if (!response.ok) {
        const errData = await response.json();
        setError(errData.detail || 'Something went wrong.');
        setLoading(false);
        return;
      }

      const data = await response.json();
      setPlan(data);
    } catch (err) {
      setError('Could not reach backend. Is it running on port 8000?');
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <h1>🥗 NutriPlan AI</h1>
      <p className="subtitle">BMR-based meal planning with nutritional guardrails</p>

      <div className="form-box">
        {/* ─── BODY STATS ─── */}
        <h3>Your Body Stats</h3>
        <div className="inputs">
          <label>
            Age
            <input type="number" value={age} onChange={e => setAge(Number(e.target.value))} />
          </label>
          <label>
            Gender
            <select value={gender} onChange={e => setGender(e.target.value)}>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </label>
          <label>
            Height (cm)
            <input type="number" value={height} onChange={e => setHeight(Number(e.target.value))} />
          </label>
          <label>
            Weight (kg)
            <input type="number" value={weight} onChange={e => setWeight(Number(e.target.value))} />
          </label>
        </div>

        <h3>Activity Level</h3>
        <select
          className="full-select"
          value={activityLevel}
          onChange={e => setActivityLevel(e.target.value)}
        >
          {activityOptions.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>

        {/* ─── DIET ─── */}
        <h3>Diet Preferences</h3>
        <div className="chips">
          {prefOptions.map(p => (
            <button
              key={p.value}
              onClick={() => toggle(preferences, setPreferences, p.value)}
              className={preferences.includes(p.value) ? 'chip chip-active' : 'chip'}
            >
              {p.label}
            </button>
          ))}
        </div>

        <h3>Exclude Allergens</h3>
        <div className="chips">
          {allergenOptions.map(a => (
            <button
              key={a.value}
              onClick={() => toggle(allergens, setAllergens, a.value)}
              className={allergens.includes(a.value) ? 'chip chip-danger' : 'chip'}
            >
              {a.label}
            </button>
          ))}
        </div>

        <h3>Protein Goal</h3>
        <div className="chips">
          {proteinOptions.map(level => (
            <button
              key={level.value}
              onClick={() => setProteinLevel(level.value)}
              className={proteinLevel === level.value ? 'chip chip-protein' : 'chip'}
            >
              {level.label}
            </button>
          ))}
        </div>

        <h3>Budget & Duration</h3>
        <div className="inputs">
          <label>
            Budget / day (₹)
            <input type="number" value={budget} onChange={e => setBudget(Number(e.target.value))} />
          </label>
          <label>
            Days
            <input type="number" value={days} onChange={e => setDays(Number(e.target.value))} />
          </label>
        </div>

        <button className="generate-btn" onClick={handleGenerate} disabled={loading}>
          {loading ? 'Calculating...' : 'Generate My Plan →'}
        </button>
      </div>

      {error && (
        <div className="error-box">
          <strong>❌ Error:</strong> {error}
        </div>
      )}

      {plan && (
        <div>
          {/* ─── NUTRITION PROFILE (NEW) ─── */}
          <div className="profile-box">
            <h3>🧬 Your Nutrition Profile</h3>
            <div className="profile-grid">
              <div><span className="label">BMR</span><span className="value">{plan.profile.bmr} cal</span></div>
              <div><span className="label">TDEE</span><span className="value">{plan.profile.tdee} cal</span></div>
              <div><span className="label">Calorie Target</span><span className="value">{plan.profile.calorie_target} cal</span></div>
              <div><span className="label">Protein Target</span><span className="value">{plan.profile.protein_target}g</span></div>
            </div>
            <p className="profile-explain">{plan.profile.explanation}</p>
          </div>

          {plan.guardrail_flags.length > 0 && (
            <div className="guardrail-box">
              <strong>⚠️ Plan Alerts</strong>
              <ul>
                {plan.guardrail_flags.map((flag, i) => <li key={i}>{flag}</li>)}
              </ul>
            </div>
          )}

          <div className="summary-box">
            <strong>📊 Summary</strong>
            <p>
              {plan.days.length} days &nbsp;|&nbsp;
              ₹{plan.total_cost} total &nbsp;|&nbsp;
              {plan.total_calories} calories &nbsp;|&nbsp;
              {plan.avg_protein}g avg protein/day
            </p>
          </div>

          {plan.days.map((day) => (
            <div key={day.day_number} className="day-card">
              <h3>
                Day {day.day_number}
                <span className="day-stats">
                  {day.day_calories} cal | ₹{day.day_cost} | {day.day_protein}g protein
                </span>
              </h3>

              <div className="meals-row">
                <MealCard meal={day.breakfast} />
                <MealCard meal={day.snack1} />
                <MealCard meal={day.lunch} />
                <MealCard meal={day.snack2} />
                <MealCard meal={day.dinner} />
              </div>

              {day.flags.length > 0 && (
                <div className="day-flags">
                  {day.flags.map((f, i) => <div key={i}>⚠️ {f}</div>)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MealCard({ meal }) {
  return (
    <div className="meal-card">
      <div className="meal-name">{meal.name}</div>
      <div className="meal-category">{meal.category}</div>
      <div className="meal-stats">
        {meal.calories} cal | {meal.protein}g protein | ₹{meal.cost}
      </div>
      <div className="meal-reason">{meal.reason}</div>
    </div>
  );
}

export default App;