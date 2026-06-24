import type { MealPlanEntry, ActivityEntry } from '@/lib/api'

interface MealPlanSectionProps {
  mealPlan: MealPlanEntry[]
  activity: ActivityEntry[]
}

const MEAL_ORDER = ['B', 'S1', 'L', 'S2', 'D']
const MEAL_HEADERS: Record<string, string> = {
  B:  '🌅 Breakfast',
  S1: 'Snack 1',
  L:  '☀️ Lunch',
  S2: 'Snack 2',
  D:  '🌙 Dinner',
}
const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function toLocalDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function getThisWeekDates(): string[] {
  const now = new Date()
  const day = now.getDay()
  const monday = new Date(now)
  monday.setDate(now.getDate() - ((day + 6) % 7))
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    return toLocalDate(d)
  })
}

export function MealPlanSection({ mealPlan, activity }: MealPlanSectionProps) {
  const weekDates = getThisWeekDates()
  const activityMap = new Map(activity.map((e) => [e.date, e]))
  const today = toLocalDate(new Date())

  const planByDate = new Map<string, Map<string, MealPlanEntry>>()
  for (const entry of mealPlan) {
    if (!planByDate.has(entry.date)) planByDate.set(entry.date, new Map())
    planByDate.get(entry.date)!.set(entry.meal_code, entry)
  }

  const daysWithPlan = weekDates.filter((d) => planByDate.has(d))

  if (daysWithPlan.length === 0) {
    return (
      <p className="text-sm text-[#8b949e]">
        No meal plan for this week. Use <code className="font-mono text-xs">/meal-plan</code> to generate one.
      </p>
    )
  }

  return (
    <div className="rounded-lg border border-[#30363d] overflow-hidden">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-[#30363d] bg-[#161b22]">
            {/* Day column */}
            <th className="text-left px-4 py-2.5 text-xs font-semibold text-[#8b949e] uppercase tracking-wide w-24">Day</th>
            {MEAL_ORDER.map((code) => (
              <th key={code} className="text-left px-4 py-2.5 text-xs font-semibold text-[#8b949e] uppercase tracking-wide">
                {MEAL_HEADERS[code]}
              </th>
            ))}
            {/* Totals column */}
            <th className="text-right px-4 py-2.5 text-xs font-semibold text-[#8b949e] uppercase tracking-wide w-32">Totals</th>
          </tr>
        </thead>
        <tbody>
          {daysWithPlan.map((date, rowIdx) => {
            const dayMeals = planByDate.get(date)!
            const actual = activityMap.get(date)
            const isToday = date === today
            const dayIdx = weekDates.indexOf(date)
            const dayName = DAY_NAMES[dayIdx] ?? date.slice(5)

            const plannedCal = MEAL_ORDER.reduce((s, code) => s + (dayMeals.get(code)?.calories ?? 0), 0)
            const plannedProtein = MEAL_ORDER.reduce((s, code) => s + (dayMeals.get(code)?.protein ?? 0), 0)
            const actualCal = actual?.calories ?? null
            const actualProtein = actual?.protein ?? null

            return (
              <tr
                key={date}
                className={`border-b border-[#21262d] last:border-0 ${
                  rowIdx % 2 === 0 ? 'bg-[#0d1117]' : 'bg-[#161b22]/50'
                } ${isToday ? 'ring-1 ring-inset ring-[#388bfd]/30' : ''}`}
              >
                {/* Day label */}
                <td className="px-4 py-3 align-top">
                  <p className={`font-semibold ${isToday ? 'text-[#388bfd]' : 'text-[#c9d1d9]'}`}>{dayName}</p>
                  <p className="text-[11px] text-[#8b949e]">{date.slice(5)}</p>
                </td>

                {/* Meal cells */}
                {MEAL_ORDER.map((code) => {
                  const meal = dayMeals.get(code)
                  return (
                    <td key={code} className="px-4 py-3 align-top">
                      {meal ? (
                        <div>
                          <p className="text-[#c9d1d9] leading-snug text-xs">{meal.name}</p>
                          {meal.calories && (
                            <p className="text-[11px] text-[#8b949e] mt-0.5">
                              {meal.calories} cal
                              {meal.protein ? <span className="text-[#3fb950]"> · {meal.protein}g</span> : null}
                            </p>
                          )}
                        </div>
                      ) : (
                        <span className="text-[#8b949e] text-xs">—</span>
                      )}
                    </td>
                  )
                })}

                {/* Totals */}
                <td className="px-4 py-3 align-top text-right">
                  <p className="text-xs text-[#c9d1d9]">{plannedCal} cal</p>
                  <p className="text-[11px] text-[#3fb950]">{plannedProtein}g protein</p>
                  {actualCal != null && (
                    <p className="text-[11px] mt-1" style={{ color: actualCal <= plannedCal ? '#3fb950' : '#f85149' }}>
                      actual: {actualCal} cal
                      {actualProtein != null ? ` · ${actualProtein}g` : ''}
                    </p>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
