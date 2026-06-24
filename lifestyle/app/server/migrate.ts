/**
 * One-time migration from ~/fitness/data.js and ~/fitness/strength.js to SQLite.
 * Safe to run multiple times — uses INSERT OR IGNORE.
 */
import { readFileSync } from 'fs'
import { join } from 'path'
import db from './db'

const FITNESS_DIR = join(process.env.HOME!, 'fitness')

// ---------------------------------------------------------------------------
// Parse ~/fitness/data.js
// ---------------------------------------------------------------------------
function loadDataJs(): Record<string, {
  weights: boolean
  running: boolean
  ateWell: boolean
  notes: string
}> {
  const raw = readFileSync(join(FITNESS_DIR, 'data.js'), 'utf8')
  const json = raw
    .replace(/^\/\/.*\n/gm, '')           // strip comments
    .replace(/window\.FITNESS_DATA\s*=\s*/, '') // strip var assignment
    .replace(/;\s*$/, '')                  // strip trailing semicolon
    .trim()
  return JSON.parse(json)
}

// ---------------------------------------------------------------------------
// Parse ~/fitness/strength.js
// ---------------------------------------------------------------------------
function loadStrengthJs(): Record<string, {
  name: string
  entries: {
    date: string
    sets?: number[]
    reps?: number[]
    notes?: string
  }[]
}> {
  const raw = readFileSync(join(FITNESS_DIR, 'strength.js'), 'utf8')
  const json = raw
    .replace(/^\/\/.*\n/gm, '')
    .replace(/window\.STRENGTH_DATA\s*=\s*/, '')
    .replace(/;\s*$/, '')
    .trim()
  return JSON.parse(json)
}

// ---------------------------------------------------------------------------
// Parse nutrition from notes string
// ---------------------------------------------------------------------------
function parseNutrition(notes: string) {
  const m = notes.match(
    /Nutrition:.*?~?(\d+(?:\.\d+)?)\s*cal,\s*(\d+(?:\.\d+)?)g protein,\s*(\d+(?:\.\d+)?)g fat,\s*(\d+(?:\.\d+)?)g carbs/i
  )
  if (!m) return { calories: null, protein: null, fat: null, carbs: null }
  return {
    calories: parseFloat(m[1]),
    protein: parseFloat(m[2]),
    fat: parseFloat(m[3]),
    carbs: parseFloat(m[4]),
  }
}

// ---------------------------------------------------------------------------
// Migrate activity_log
// ---------------------------------------------------------------------------
function migrateActivity(data: ReturnType<typeof loadDataJs>) {
  let count = 0
  for (const [date, entry] of Object.entries(data)) {
    const { calories, protein, fat, carbs } = parseNutrition(entry.notes || '')
    const result = db.run(
      `INSERT OR IGNORE INTO activity_log
         (date, weights, running, ate_well, notes, calories, protein, fat, carbs)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        date,
        entry.weights ? 1 : 0,
        entry.running ? 1 : 0,
        entry.ateWell ? 1 : 0,
        entry.notes || '',
        calories,
        protein,
        fat,
        carbs,
      ]
    )
    if (result.changes > 0) count++
  }
  console.log(`✅ Migrated ${count} activity entries (${Object.keys(data).length - count} already existed)`)
}

// ---------------------------------------------------------------------------
// Migrate exercises + strength entries
// ---------------------------------------------------------------------------
function migrateStrength(data: ReturnType<typeof loadStrengthJs>) {
  let exerciseCount = 0
  let entryCount = 0

  for (const [slug, exercise] of Object.entries(data)) {
    // Upsert exercise
    db.run('INSERT OR IGNORE INTO exercises (slug, name) VALUES (?, ?)', [slug, exercise.name])
    const ex = db.query('SELECT id FROM exercises WHERE slug = ?').get(slug) as { id: number }
    exerciseCount++

    for (const entry of exercise.entries) {
      // Check if this entry already exists (same exercise + date)
      const existing = db
        .query('SELECT id FROM strength_entries WHERE exercise_id = ? AND date = ?')
        .get(ex.id, entry.date) as { id: number } | null

      if (existing) continue

      const result = db.run(
        'INSERT INTO strength_entries (exercise_id, date, notes) VALUES (?, ?, ?)',
        [ex.id, entry.date, entry.notes ?? null]
      )
      const entryId = result.lastInsertRowid as number
      entryCount++

      const sets = entry.sets ?? []
      const reps = entry.reps ?? []

      sets.forEach((weight, i) => {
        db.run(
          'INSERT INTO strength_sets (entry_id, set_order, weight, reps) VALUES (?, ?, ?, ?)',
          [entryId, i + 1, weight, reps[i] ?? null]
        )
      })

      // If no sets but reps exist (e.g. pull-ups bodyweight)
      if (sets.length === 0 && reps.length > 0) {
        reps.forEach((rep, i) => {
          db.run(
            'INSERT INTO strength_sets (entry_id, set_order, weight, reps) VALUES (?, ?, ?, ?)',
            [entryId, i + 1, null, rep]
          )
        })
      }
    }
  }

  console.log(`✅ Migrated ${exerciseCount} exercises, ${entryCount} strength entries`)
}

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------
console.log('🚀 Starting migration from ~/fitness/ to SQLite...')

const activityData = loadDataJs()
const strengthData = loadStrengthJs()

migrateActivity(activityData)
migrateStrength(strengthData)

console.log('🎉 Migration complete!')
