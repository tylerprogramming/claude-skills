import { Hono } from 'hono'
import db from '../db'

const app = new Hono()

function parseMiles(notes: string): number {
  const match = notes.match(/(\d+(?:\.\d+)?)\s*mi/i)
  return match ? parseFloat(match[1]) : 0
}

// GET /api/stats
app.get('/', (c) => {
  const rows = db
    .query('SELECT * FROM activity_log ORDER BY date ASC')
    .all() as {
    date: string
    weights: number
    running: number
    ate_well: number
    notes: string
    calories: number | null
    protein: number | null
  }[]

  let totalMiles = 0
  let runningDays = 0
  let weightDays = 0
  let streak = 0
  let bestStreak = 0
  let currentStreak = 0
  let calSum = 0
  let calCount = 0
  let proteinSum = 0
  let proteinCount = 0

  const today = new Date().toISOString().split('T')[0]
  let prevDate: string | null = null

  for (const row of rows) {
    if (row.running) {
      runningDays++
      totalMiles += parseMiles(row.notes || '')
    }
    if (row.weights) weightDays++

    if (row.calories != null) {
      calSum += row.calories
      calCount++
    }
    if (row.protein != null) {
      proteinSum += row.protein
      proteinCount++
    }

    // Streak: consecutive days with any activity
    const hasActivity = row.running || row.weights
    if (hasActivity) {
      if (prevDate) {
        const prev = new Date(prevDate)
        const curr = new Date(row.date)
        const diff = (curr.getTime() - prev.getTime()) / (1000 * 60 * 60 * 24)
        if (diff === 1) {
          currentStreak++
        } else {
          currentStreak = 1
        }
      } else {
        currentStreak = 1
      }
      if (currentStreak > bestStreak) bestStreak = currentStreak
      prevDate = row.date
    } else {
      currentStreak = 0
      prevDate = row.date
    }
  }

  // Current streak (from today backwards)
  const sortedActive = rows.filter((r) => r.running || r.weights).map((r) => r.date).reverse()
  streak = 0
  let expected = today
  for (const date of sortedActive) {
    if (date === expected) {
      streak++
      const d = new Date(expected)
      d.setDate(d.getDate() - 1)
      expected = d.toISOString().split('T')[0]
    } else {
      break
    }
  }

  const runEntries = rows.filter((r) => r.running)
  const avgMilesPerRun = runEntries.length > 0 ? totalMiles / runEntries.length : 0

  return c.json({
    totalMiles: Math.round(totalMiles * 100) / 100,
    runningDays,
    weightDays,
    streak,
    bestStreak,
    avgMilesPerRun: Math.round(avgMilesPerRun * 100) / 100,
    avgCalories: calCount > 0 ? Math.round(calSum / calCount) : 0,
    avgProtein: proteinCount > 0 ? Math.round(proteinSum / proteinCount) : 0,
  })
})

export default app
