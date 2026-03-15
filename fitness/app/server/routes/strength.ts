import { Hono } from 'hono'
import db from '../db'

const app = new Hono()

// GET /api/strength — all exercises with their entries and sets
app.get('/', (c) => {
  const exercises = db.query('SELECT * FROM exercises ORDER BY name').all() as {
    id: number
    slug: string
    name: string
  }[]

  const result = exercises.map((ex) => {
    const entries = db
      .query('SELECT * FROM strength_entries WHERE exercise_id = ? ORDER BY date DESC')
      .all(ex.id) as { id: number; date: string; notes: string; created_at: string }[]

    const entriesWithSets = entries.map((entry) => {
      const sets = db
        .query('SELECT * FROM strength_sets WHERE entry_id = ? ORDER BY set_order')
        .all(entry.id) as { id: number; set_order: number; weight: number | null; reps: number | null }[]
      return { ...entry, sets }
    })

    return { ...ex, entries: entriesWithSets }
  })

  return c.json(result)
})

// POST /api/strength/:slug — add entry
app.post('/:slug', async (c) => {
  const slug = c.req.param('slug')
  const body = await c.req.json<{
    date: string
    notes?: string
    sets: { weight?: number; reps?: number }[]
  }>()

  const exercise = db.query('SELECT * FROM exercises WHERE slug = ?').get(slug) as { id: number } | null
  if (!exercise) return c.json({ error: 'Exercise not found' }, 404)

  const result = db.run(
    'INSERT INTO strength_entries (exercise_id, date, notes) VALUES (?, ?, ?)',
    [exercise.id, body.date, body.notes ?? null]
  )
  const entryId = result.lastInsertRowid as number

  body.sets.forEach((set, i) => {
    db.run(
      'INSERT INTO strength_sets (entry_id, set_order, weight, reps) VALUES (?, ?, ?, ?)',
      [entryId, i + 1, set.weight ?? null, set.reps ?? null]
    )
  })

  return c.json({ success: true, entryId })
})

export default app
