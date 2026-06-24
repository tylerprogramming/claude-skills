import { Database } from 'bun:sqlite'

const db = new Database('fitness.db')

db.run(`
  CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    weights INTEGER NOT NULL DEFAULT 0,
    running INTEGER NOT NULL DEFAULT 0,
    ate_well INTEGER NOT NULL DEFAULT 0,
    notes TEXT DEFAULT '',
    calories REAL,
    protein REAL,
    fat REAL,
    carbs REAL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
  )
`)

db.run(`
  CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL
  )
`)

db.run(`
  CREATE TABLE IF NOT EXISTS strength_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id),
    date TEXT NOT NULL,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  )
`)

db.run(`
  CREATE TABLE IF NOT EXISTS strength_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL REFERENCES strength_entries(id),
    set_order INTEGER NOT NULL,
    weight REAL,
    reps INTEGER
  )
`)

db.run(`
  CREATE TABLE IF NOT EXISTS meal_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    meal_code TEXT NOT NULL,
    name TEXT NOT NULL,
    calories INTEGER,
    protein INTEGER,
    completed INTEGER NOT NULL DEFAULT 0,
    UNIQUE(date, meal_code)
  )
`)

db.run(`
  CREATE TABLE IF NOT EXISTS nutrition_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    serving_size TEXT NOT NULL,
    calories REAL NOT NULL DEFAULT 0,
    protein REAL NOT NULL DEFAULT 0,
    fat REAL NOT NULL DEFAULT 0,
    carbs REAL NOT NULL DEFAULT 0,
    sodium REAL DEFAULT 0,
    fiber REAL DEFAULT 0,
    sugar REAL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  )
`)

// Migrate: add completed column if it doesn't exist yet
try {
  db.run('ALTER TABLE meal_plan ADD COLUMN completed INTEGER NOT NULL DEFAULT 0')
} catch {
  // Column already exists — ignore
}

export default db
