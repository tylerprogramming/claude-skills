import { Hono } from 'hono'
import db from '../db'

const app = new Hono()

// GET /api/meal-plan — current week's plan
app.get('/', (c) => {
  const now = new Date()
  const day = now.getDay()
  const monday = new Date(now)
  monday.setDate(now.getDate() - ((day + 6) % 7))
  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)
  // Extend by one day so "tomorrow" is always included (e.g. Sunday → next Monday)
  const endDate = new Date(sunday)
  endDate.setDate(sunday.getDate() + 1)

  const start = monday.toISOString().split('T')[0]
  const end = endDate.toISOString().split('T')[0]

  const rows = db
    .query('SELECT * FROM meal_plan WHERE date >= ? AND date <= ? ORDER BY date, meal_code')
    .all(start, end) as { date: string; meal_code: string; name: string; calories: number | null; protein: number | null; completed: number }[]

  return c.json(rows.map((r) => ({ ...r, completed: Boolean(r.completed) })))
})

// POST /api/meal-plan — upsert entries
app.post('/', async (c) => {
  const body = await c.req.json<
    { date: string; meal_code: string; name: string; calories?: number; protein?: number }[]
  >()

  for (const entry of body) {
    db.run(
      `INSERT INTO meal_plan (date, meal_code, name, calories, protein)
       VALUES (?, ?, ?, ?, ?)
       ON CONFLICT(date, meal_code) DO UPDATE SET
         name = excluded.name,
         calories = excluded.calories,
         protein = excluded.protein`,
      [entry.date, entry.meal_code, entry.name, entry.calories ?? null, entry.protein ?? null]
    )
  }

  return c.json({ success: true })
})

// POST /api/meal-plan/toggle — toggle completed for a specific meal
app.post('/toggle', async (c) => {
  const { date, meal_code } = await c.req.json<{ date: string; meal_code: string }>()

  const row = db
    .query('SELECT completed FROM meal_plan WHERE date = ? AND meal_code = ?')
    .get(date, meal_code) as { completed: number } | null

  if (!row) return c.json({ error: 'Not found' }, 404)

  const newVal = row.completed ? 0 : 1
  db.run('UPDATE meal_plan SET completed = ? WHERE date = ? AND meal_code = ?', [newVal, date, meal_code])

  return c.json({ completed: Boolean(newVal) })
})

export default app
