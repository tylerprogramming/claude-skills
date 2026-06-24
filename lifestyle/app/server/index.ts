import { Hono } from 'hono'
import { serve } from '@hono/node-server'
import { cors } from 'hono/cors'
import activityRoutes from './routes/activity'
import strengthRoutes from './routes/strength'
import mealPlanRoutes from './routes/meal-plan'
import statsRoutes from './routes/stats'
import nutritionRoutes from './routes/nutrition'

// Initialize DB (creates tables if needed)
import './db'

const app = new Hono()

app.use('*', cors())

app.route('/api/activity', activityRoutes)
app.route('/api/strength', strengthRoutes)
app.route('/api/meal-plan', mealPlanRoutes)
app.route('/api/stats', statsRoutes)
app.route('/api/nutrition', nutritionRoutes)

app.get('/api/health', (c) => c.json({ ok: true }))

const PORT = 3001

serve({ fetch: app.fetch, port: PORT }, () => {
  console.log(`🏃 Fitness API running on http://localhost:${PORT}`)
})
