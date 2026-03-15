import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { MealPlanEntry, ActivityEntry } from '@/lib/api'
import { toggleMeal } from '@/lib/api'

interface TodayTomorrowMealsProps {
  mealPlan: MealPlanEntry[]
  activity: ActivityEntry[]
  onMealToggled?: (date: string, meal_code: string, completed: boolean) => void
}

const MEAL_ORDER = ['B', 'S1', 'L', 'S2', 'D']
const MEAL_LABELS: Record<string, string> = {
  B:  '🌅 Breakfast',
  S1: 'Snack 1',
  L:  '☀️ Lunch',
  S2: 'Snack 2',
  D:  '🌙 Dinner',
}

function DayCard({
  label,
  date,
  meals,
  actualCal,
  actualProtein,
  isToday,
  onToggle,
}: {
  label: string
  date: string
  meals: MealPlanEntry[]
  actualCal?: number | null
  actualProtein?: number | null
  isToday: boolean
  onToggle: (meal_code: string) => void
}) {
  const ordered = MEAL_ORDER
    .map((code) => meals.find((m) => m.meal_code === code))
    .filter(Boolean) as MealPlanEntry[]

  const plannedCal = ordered.reduce((s, m) => s + (m.calories ?? 0), 0)
  const plannedProtein = ordered.reduce((s, m) => s + (m.protein ?? 0), 0)

  return (
    <Card className="bg-[#161b22] border-[#30363d] flex-1">
      <CardHeader className="pb-2 pt-4 px-5">
        <div className="flex items-baseline justify-between">
          <CardTitle className="text-base font-semibold text-[#c9d1d9]">{label}</CardTitle>
          <span className="text-xs text-[#8b949e]">{date.slice(5)}</span>
        </div>
      </CardHeader>
      <CardContent className="px-5 pb-4 space-y-2.5">
        {ordered.map((meal) => {
          const done = meal.completed ?? false
          return (
            <div
              key={meal.meal_code}
              className={`flex justify-between items-start gap-3 rounded-md transition-opacity ${
                isToday ? 'cursor-pointer hover:bg-[#21262d] -mx-2 px-2 py-1' : 'py-0.5'
              } ${done ? 'opacity-50' : ''}`}
              onClick={() => isToday && onToggle(meal.meal_code)}
              title={isToday ? (done ? 'Click to unmark' : 'Click to mark as eaten') : undefined}
            >
              <div className="flex-1 min-w-0">
                <p className="text-[10px] text-[#8b949e] uppercase tracking-wide leading-none mb-0.5">
                  {MEAL_LABELS[meal.meal_code] ?? meal.meal_code}
                </p>
                <p className={`text-sm text-[#c9d1d9] leading-snug ${done ? 'line-through decoration-[#8b949e]' : ''}`}>
                  {meal.name}
                </p>
              </div>
              <div className="text-right flex-shrink-0 flex items-center gap-2">
                {meal.calories && (
                  <div>
                    <p className="text-xs text-[#8b949e]">{meal.calories} cal</p>
                    {meal.protein && <p className="text-xs text-[#3fb950]">{meal.protein}g</p>}
                  </div>
                )}
                {isToday && (
                  <span className={`text-base leading-none ${done ? 'opacity-100' : 'opacity-20'}`}>✓</span>
                )}
              </div>
            </div>
          )
        })}

        {/* Totals */}
        <div className="pt-2 border-t border-[#21262d] space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-[#8b949e]">Planned</span>
            <span className="text-[#c9d1d9]">{plannedCal} cal · {plannedProtein}g protein</span>
          </div>
          {actualCal != null && (
            <div className="flex justify-between text-xs">
              <span className="text-[#8b949e]">Actual</span>
              <span style={{ color: actualCal <= plannedCal ? '#3fb950' : '#f85149' }}>
                {actualCal} cal{actualProtein != null ? ` · ${actualProtein}g protein` : ''}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function TodayTomorrowMeals({ mealPlan, activity, onMealToggled }: TodayTomorrowMealsProps) {
  const toLocalDate = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  const today = toLocalDate(new Date())
  const tomorrow = toLocalDate(new Date(Date.now() + 86400000))

  // Local optimistic state for completed toggles
  const [completedOverrides, setCompletedOverrides] = useState<Record<string, boolean>>({})

  const planByDate = new Map<string, MealPlanEntry[]>()
  for (const entry of mealPlan) {
    if (!planByDate.has(entry.date)) planByDate.set(entry.date, [])
    planByDate.get(entry.date)!.push(entry)
  }

  // Apply local overrides
  const applyOverrides = (meals: MealPlanEntry[], date: string): MealPlanEntry[] =>
    meals.map((m) => {
      const key = `${date}:${m.meal_code}`
      return key in completedOverrides ? { ...m, completed: completedOverrides[key] } : m
    })

  const activityMap = new Map(activity.map((e) => [e.date, e]))

  const todayMeals = applyOverrides(planByDate.get(today) ?? [], today)
  const tomorrowMeals = applyOverrides(planByDate.get(tomorrow) ?? [], tomorrow)
  const todayActivity = activityMap.get(today)
  const tomorrowActivity = activityMap.get(tomorrow)

  const handleToggle = async (date: string, meal_code: string) => {
    const key = `${date}:${meal_code}`
    const current = completedOverrides[key] ?? (planByDate.get(date)?.find((m) => m.meal_code === meal_code)?.completed ?? false)
    // Optimistic update
    setCompletedOverrides((prev) => ({ ...prev, [key]: !current }))
    try {
      const result = await toggleMeal(date, meal_code)
      setCompletedOverrides((prev) => ({ ...prev, [key]: result.completed }))
      onMealToggled?.(date, meal_code, result.completed)
    } catch {
      // Revert on error
      setCompletedOverrides((prev) => ({ ...prev, [key]: current }))
    }
  }

  if (todayMeals.length === 0 && tomorrowMeals.length === 0) {
    return <p className="text-sm text-[#8b949e]">No meal plan for today or tomorrow.</p>
  }

  return (
    <div className="flex gap-4">
      {todayMeals.length > 0 && (
        <DayCard
          label="Today"
          date={today}
          meals={todayMeals}
          actualCal={todayActivity?.calories}
          actualProtein={todayActivity?.protein}
          isToday={true}
          onToggle={(code) => handleToggle(today, code)}
        />
      )}
      {tomorrowMeals.length > 0 && (
        <DayCard
          label="Tomorrow"
          date={tomorrow}
          meals={tomorrowMeals}
          actualCal={tomorrowActivity?.calories}
          actualProtein={tomorrowActivity?.protein}
          isToday={false}
          onToggle={() => {}}
        />
      )}
    </div>
  )
}
