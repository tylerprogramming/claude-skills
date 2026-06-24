import { Hono } from 'hono'
import db from '../db'

const app = new Hono()

// GET /api/nutrition — all items
app.get('/', (c) => {
  const rows = db.query('SELECT * FROM nutrition_items ORDER BY name').all()
  return c.json(rows)
})

// GET /api/nutrition/search?q=flounder — search by name
app.get('/search', (c) => {
  const q = c.req.query('q') ?? ''
  const rows = db
    .query('SELECT * FROM nutrition_items WHERE name LIKE ? ORDER BY name')
    .all(`%${q}%`)
  return c.json(rows)
})

// POST /api/nutrition — create item
app.post('/', async (c) => {
  const body = await c.req.json<{
    name: string
    serving_size: string
    calories: number
    protein: number
    fat: number
    carbs: number
    sodium?: number
    fiber?: number
    sugar?: number
  }>()

  const result = db.run(
    `INSERT INTO nutrition_items (name, serving_size, calories, protein, fat, carbs, sodium, fiber, sugar)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      body.name,
      body.serving_size,
      body.calories,
      body.protein,
      body.fat,
      body.carbs,
      body.sodium ?? 0,
      body.fiber ?? 0,
      body.sugar ?? 0,
    ]
  )

  return c.json({ id: Number(result.lastInsertRowid), ...body }, 201)
})

// PUT /api/nutrition/:id — update item
app.put('/:id', async (c) => {
  const id = c.req.param('id')
  const body = await c.req.json<{
    name?: string
    serving_size?: string
    calories?: number
    protein?: number
    fat?: number
    carbs?: number
    sodium?: number
    fiber?: number
    sugar?: number
  }>()

  const fields: string[] = []
  const values: (string | number)[] = []

  for (const [key, val] of Object.entries(body)) {
    if (val !== undefined) {
      fields.push(`${key} = ?`)
      values.push(val)
    }
  }

  if (fields.length === 0) return c.json({ error: 'No fields to update' }, 400)

  values.push(Number(id))
  db.run(`UPDATE nutrition_items SET ${fields.join(', ')} WHERE id = ?`, values)

  const updated = db.query('SELECT * FROM nutrition_items WHERE id = ?').get(Number(id))
  return c.json(updated)
})

// DELETE /api/nutrition/:id — delete item
app.delete('/:id', (c) => {
  const id = c.req.param('id')
  db.run('DELETE FROM nutrition_items WHERE id = ?', [Number(id)])
  return c.json({ success: true })
})

export default app
