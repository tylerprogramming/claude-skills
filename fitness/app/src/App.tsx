import { useEffect, useState } from 'react'
import { getActivity, getStats, getMealPlan, getStrength, getNutritionItems } from '@/lib/api'
import type { ActivityEntry, Stats, MealPlanEntry, Exercise, NutritionItem } from '@/lib/api'
import { ActivityGrid } from '@/components/ActivityGrid'
import { StatsCards } from '@/components/StatsCards'
import { DayModal } from '@/components/DayModal'
import { StrengthCharts } from '@/components/StrengthCharts'
import { MealPlanSection } from '@/components/MealPlanSection'
import { TodayTomorrowMeals } from '@/components/TodayTomorrowMeals'
import { NutritionSection } from '@/components/NutritionSection'

type Tab = 'overview' | 'strength' | 'meal-plan' | 'nutrition'

const TABS: { id: Tab; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'meal-plan', label: 'Meal Plan' },
  { id: 'strength', label: 'Strength' },
  { id: 'nutrition', label: 'Nutrition DB' },
]

export default function App() {
  const [activity, setActivity] = useState<ActivityEntry[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [mealPlan, setMealPlan] = useState<MealPlanEntry[]>([])
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [nutritionItems, setNutritionItems] = useState<NutritionItem[]>([])
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('overview')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([getActivity(), getStats(), getMealPlan(), getStrength(), getNutritionItems()])
      .then(([act, st, mp, ex, ni]) => {
        setActivity(act)
        setStats(st)
        setMealPlan(mp)
        setExercises(ex)
        setNutritionItems(ni)
      })
      .catch(() => setError('Could not connect to server. Run: bun run dev:server'))
      .finally(() => setLoading(false))
  }, [])

  const totalWorkouts = activity.filter((e) => e.running || e.weights).length

  return (
    <div className="dark min-h-screen bg-[#0d1117] text-[#c9d1d9]">
      <div className="max-w-[1200px] mx-auto px-6 py-10">
        <div className="flex gap-10">

          {/* Sidebar */}
          <aside className="w-[260px] flex-shrink-0 flex flex-col gap-4">
            <div className="relative w-[260px] h-[260px]">
              <img
                src="/profile.png"
                alt="Tyler Reed"
                className="w-[260px] h-[260px] rounded-full object-cover border-4 border-[#388bfd] bg-[#161b22]"
              />
              <div className="absolute bottom-4 right-4 bg-[#0d1117] rounded-full p-1 border-2 border-[#30363d]">
                <div className="w-8 h-8 bg-[#3fb950] rounded-full flex items-center justify-center text-base">🏃</div>
              </div>
            </div>

            <div>
              <h1 className="text-2xl font-semibold text-[#c9d1d9]">Tyler Reed</h1>
              <p className="text-lg text-[#8b949e] -mt-1">@fitness_journey</p>
            </div>

            <p className="text-sm text-[#8b949e] leading-relaxed">
              Building consistency one workout at a time. Running, lifting, and trying to eat well. Tracking my progress with code.
            </p>

            <div className="flex gap-2 items-center text-sm text-[#8b949e]">
              <span><strong className="text-[#c9d1d9]">{stats?.totalMiles.toFixed(1) ?? '—'}</strong> miles</span>
              <span className="text-[#30363d]">·</span>
              <span><strong className="text-[#c9d1d9]">{totalWorkouts}</strong> workouts</span>
            </div>

            <div className="flex flex-col gap-2 pt-4 border-t border-[#21262d] text-sm text-[#8b949e]">
              <div className="flex items-center gap-2">
                <span className="w-4 text-center">🔥</span>
                <span><strong className="text-[#c9d1d9]">{stats?.streak ?? 0}</strong> day streak</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-4 text-center">🏆</span>
                <span>Best: <strong className="text-[#c9d1d9]">{stats?.bestStreak ?? 0}</strong> days</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-4 text-center">📍</span>
                <span>Tampa, FL</span>
              </div>
            </div>

            <div className="pt-4 border-t border-[#21262d]">
              <h3 className="text-sm font-semibold text-[#c9d1d9] mb-3">Achievements</h3>
              <div className="flex gap-2 flex-wrap">
                {[
                  { label: 'Running', emoji: '🏃', color: 'from-[#388bfd] to-[#1f6feb]', count: stats?.runningDays ?? 0 },
                  { label: 'Weights', emoji: '🏋️', color: 'from-[#da3633] to-[#b62324]', count: stats?.weightDays ?? 0 },
                  { label: 'Streak', emoji: '🔥', color: 'from-[#3fb950] to-[#238636]', count: stats?.bestStreak ?? 0 },
                  { label: 'Nutrition', emoji: '🥗', color: 'from-[#f0c000] to-[#d4a900]', count: activity.filter((e) => e.ateWell).length },
                ].map(({ label, emoji, color, count }) => (
                  <div key={label} className="relative" title={label}>
                    <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${color} flex items-center justify-center text-2xl`}>
                      {emoji}
                    </div>
                    <span className="absolute -bottom-0.5 -right-0.5 bg-[#0d1117] border-2 border-[#30363d] rounded-full px-1 text-[10px] font-semibold text-[#c9d1d9] leading-4">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </aside>

          {/* Main content */}
          <main className="flex-1 min-w-0 flex flex-col gap-6">

            {error && (
              <div className="rounded-md bg-red-900/20 border border-red-500/30 text-red-400 px-4 py-3 text-sm">
                {error}
              </div>
            )}

            {loading && <div className="text-sm text-[#8b949e]">Loading...</div>}

            {!loading && !error && (
              <>
                {/* Quote */}
                <div>
                  <p className="text-[#8b949e] italic text-sm">"The only bad workout is the one that didn't happen."</p>
                  <p className="text-[#6e7681] text-xs mt-1">Every square represents a day. Every color tells a story.</p>
                </div>

                {/* Workout count + tabs */}
                <div className="flex items-center justify-between">
                  <p className="text-sm text-[#c9d1d9]">
                    <strong>{totalWorkouts}</strong> workouts in the last year
                  </p>
                  <div className="flex gap-1">
                    {TABS.map(({ id, label }) => (
                      <button
                        key={id}
                        onClick={() => setTab(id)}
                        className={`px-3 py-1 text-xs rounded-md border transition-colors ${
                          tab === id
                            ? 'bg-[#238636] border-[#238636] text-white'
                            : 'bg-transparent border-[#30363d] text-[#8b949e] hover:border-[#8b949e] hover:text-[#c9d1d9]'
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>

                {tab === 'overview' && (
                  <>
                    <StatsCards stats={stats} />

                    <div className="rounded-lg border border-[#30363d] bg-[#161b22] p-4">
                      <ActivityGrid activity={activity} onDayClick={setSelectedDate} />
                    </div>

                    <section>
                      <h2 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider mb-3">
                        Today &amp; Tomorrow
                      </h2>
                      <TodayTomorrowMeals
                        mealPlan={mealPlan}
                        activity={activity}
                        onMealToggled={(date, meal_code, completed) =>
                          setMealPlan((prev) =>
                            prev.map((m) =>
                              m.date === date && m.meal_code === meal_code ? { ...m, completed } : m
                            )
                          )
                        }
                      />
                    </section>
                  </>
                )}

                {tab === 'meal-plan' && (
                  <section>
                    <h2 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider mb-3">
                      This Week's Meal Plan
                    </h2>
                    <MealPlanSection mealPlan={mealPlan} activity={activity} />
                  </section>
                )}

                {tab === 'nutrition' && (
                  <section>
                    <h2 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider mb-3">
                      Nutrition Database
                    </h2>
                    <NutritionSection
                      items={nutritionItems}
                      onUpdate={() => getNutritionItems().then(setNutritionItems)}
                    />
                  </section>
                )}

                {tab === 'strength' && (
                  <section>
                    <h2 className="text-xs font-semibold text-[#8b949e] uppercase tracking-wider mb-3">
                      Strength Progress
                    </h2>
                    <StrengthCharts exercises={exercises} activity={activity} />
                  </section>
                )}
              </>
            )}
          </main>
        </div>
      </div>

      <DayModal date={selectedDate} onClose={() => setSelectedDate(null)} />
    </div>
  )
}
