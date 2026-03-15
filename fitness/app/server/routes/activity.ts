import { Hono } from 'hono'
import db from '../db'

const app = new Hono()

// Parse nutrition from notes: "Nutrition: ~1200 cal, 80g protein, 40g fat, 120g carbs"
function parseNutrition(notes: string) {
  const match = notes.match(/Nutrition:.*?~?(\d+(?:\.\d+)?)\s*cal,\s*(\d+(?:\.\d+)?)g protein,\s*(\d+(?:\.\d+)?)g fat,\s*(\d+(?:\.\d+)?)g carbs/i)
  if (!match) return { calories: null, protein: null, fat: null, carbs: null }
  return {
    calories: parseFloat(match[1]),
    protein: parseFloat(match[2]),
    fat: parseFloat(match[3]),
    carbs: parseFloat(match[4]),
  }
}

function rowToEntry(row: Record<string, unknown>) {
  return {
    date: row.date as string,
    weights: Boolean(row.weights),
    running: Boolean(row.running),
    ateWell: Boolean(row.ate_well),
    notes: (row.notes as string) || '',
    calories: row.calories as number | null,
    protein: row.protein as number | null,
    fat: row.fat as number | null,
    carbs: row.carbs as number | null,
  }
}

// GET /api/activity — all entries sorted by date desc
app.get('/', (c) => {
  const rows = db.query('SELECT * FROM activity_log ORDER BY date DESC').all() as Record<string, unknown>[]
  return c.json(rows.map(rowToEntry))
})

// GET /api/activity/:date
app.get('/:date', (c) => {
  const date = c.req.param('date')
  const row = db.query('SELECT * FROM activity_log WHERE date = ?').get(date) as Record<string, unknown> | null
  if (!row) return c.json(null, 404)
  return c.json(rowToEntry(row))
})

// POST /api/activity — upsert
app.post('/', async (c) => {
  const body = await c.req.json<{
    date: string
    weights?: boolean
    running?: boolean
    ateWell?: boolean
    notes?: string
    calories?: number
    protein?: number
    fat?: number
    carbs?: number
  }>()

  const { date, weights = false, running = false, ateWell = false, notes = '' } = body

  // Parse nutrition from notes if not explicitly provided
  let { calories, protein, fat, carbs } = body
  if (calories == null && notes) {
    const parsed = parseNutrition(notes)
    calories = parsed.calories ?? undefined
    protein = parsed.protein ?? undefined
    fat = parsed.fat ?? undefined
    carbs = parsed.carbs ?? undefined
  }

  db.run(
    `INSERT INTO activity_log (date, weights, running, ate_well, notes, calories, protein, fat, carbs)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(date) DO UPDATE SET
       weights = excluded.weights,
       running = excluded.running,
       ate_well = excluded.ate_well,
       notes = excluded.notes,
       calories = excluded.calories,
       protein = excluded.protein,
       fat = excluded.fat,
       carbs = excluded.carbs,
       updated_at = CURRENT_TIMESTAMP`,
    [date, weights ? 1 : 0, running ? 1 : 0, ateWell ? 1 : 0, notes, calories ?? null, protein ?? null, fat ?? null, carbs ?? null]
  )

  const row = db.query('SELECT * FROM activity_log WHERE date = ?').get(date) as Record<string, unknown>
  return c.json(rowToEntry(row))
})

export default app
