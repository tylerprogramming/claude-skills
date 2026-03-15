export interface ActivityEntry {
  date: string
  weights: boolean
  running: boolean
  ateWell: boolean
  notes: string
  calories?: number
  protein?: number
  fat?: number
  carbs?: number
}

export interface StrengthSet {
  set_order: number
  weight?: number
  reps?: number
}

export interface StrengthEntry {
  id: number
  date: string
  notes?: string
  sets: StrengthSet[]
}

export interface Exercise {
  id: number
  slug: string
  name: string
  entries: StrengthEntry[]
}

export interface Stats {
  totalMiles: number
  runningDays: number
  weightDays: number
  streak: number
  bestStreak: number
  avgMilesPerRun: number
  avgCalories: number
  avgProtein: number
}

export interface MealPlanEntry {
  date: string
  meal_code: string
  name: string
  calories?: number
  protein?: number
  completed?: boolean
}

export const getActivity = (): Promise<ActivityEntry[]> =>
  fetch('/api/activity').then((r) => r.json())

export const getActivityDay = (date: string): Promise<ActivityEntry | null> =>
  fetch(`/api/activity/${date}`).then((r) => (r.ok ? r.json() : null))

export const upsertActivity = (entry: Partial<ActivityEntry> & { date: string }): Promise<ActivityEntry> =>
  fetch('/api/activity', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  }).then((r) => r.json())

export const getStrength = (): Promise<Exercise[]> =>
  fetch('/api/strength').then((r) => r.json())

export const getMealPlan = (): Promise<MealPlanEntry[]> =>
  fetch('/api/meal-plan').then((r) => r.json())

export const toggleMeal = (date: string, meal_code: string): Promise<{ completed: boolean }> =>
  fetch('/api/meal-plan/toggle', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date, meal_code }),
  }).then((r) => r.json())

export const getStats = (): Promise<Stats> =>
  fetch('/api/stats').then((r) => r.json())

// Nutrition Items
export interface NutritionItem {
  id: number
  name: string
  serving_size: string
  calories: number
  protein: number
  fat: number
  carbs: number
  sodium: number
  fiber: number
  sugar: number
}

export const getNutritionItems = (): Promise<NutritionItem[]> =>
  fetch('/api/nutrition').then((r) => r.json())

export const createNutritionItem = (item: Omit<NutritionItem, 'id'>): Promise<NutritionItem> =>
  fetch('/api/nutrition', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
  }).then((r) => r.json())

export const updateNutritionItem = (id: number, item: Partial<NutritionItem>): Promise<NutritionItem> =>
  fetch(`/api/nutrition/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
  }).then((r) => r.json())

export const deleteNutritionItem = (id: number): Promise<{ success: boolean }> =>
  fetch(`/api/nutrition/${id}`, { method: 'DELETE' }).then((r) => r.json())
