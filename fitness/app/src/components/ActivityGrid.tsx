import { useState } from 'react'
import type { ActivityEntry } from '@/lib/api'

// Colors matching original tracker
const COLORS = {
  empty: '#161b22',
  running: '#388bfd',
  weights: '#da3633',
  both: '#8957e5',
}

interface DayCell {
  date: string
  entry: ActivityEntry | null
}

interface ActivityGridProps {
  activity: ActivityEntry[]
  onDayClick: (date: string) => void
}

function getColor(entry: ActivityEntry | null): string {
  if (!entry) return COLORS.empty
  const { running, weights } = entry
  if (running && weights) return COLORS.both
  if (running) return COLORS.running
  if (weights) return COLORS.weights
  return COLORS.empty
}

function buildGrid(activity: ActivityEntry[]): DayCell[][] {
  const map = new Map(activity.map((e) => [e.date, e]))

  // Find the Sunday that starts a 52-week window ending today
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  // Start from the Sunday 52 weeks ago
  const startDate = new Date(today)
  startDate.setDate(today.getDate() - 52 * 7)
  // Roll back to Sunday
  startDate.setDate(startDate.getDate() - startDate.getDay())

  // Build columns (weeks), each column has 7 days (Sun–Sat)
  const weeks: DayCell[][] = []
  const cur = new Date(startDate)

  while (cur <= today) {
    const week: DayCell[] = []
    for (let d = 0; d < 7; d++) {
      const dateStr = cur.toISOString().split('T')[0]
      if (cur <= today) {
        week.push({ date: dateStr, entry: map.get(dateStr) ?? null })
      }
      cur.setDate(cur.getDate() + 1)
    }
    weeks.push(week)
  }

  return weeks
}

const MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

export function ActivityGrid({ activity, onDayClick }: ActivityGridProps) {
  const [tooltip, setTooltip] = useState<{ date: string; x: number; y: number } | null>(null)
  const weeks = buildGrid(activity)

  // Compute month labels
  const monthPositions: { label: string; col: number }[] = []
  weeks.forEach((week, col) => {
    const firstDay = week[0]?.date
    if (firstDay) {
      const d = new Date(firstDay)
      if (d.getDate() <= 7) {
        monthPositions.push({ label: MONTH_LABELS[d.getMonth()], col })
      }
    }
  })

  const CELL = 12
  const GAP = 2

  return (
    <div>
      <div>
        {/* Month labels */}
        <div className="flex mb-1 ml-8">
          {weeks.map((_, col) => {
            const mp = monthPositions.find((m) => m.col === col)
            return (
              <div key={col} style={{ width: CELL + GAP }} className="text-[10px] text-muted-foreground">
                {mp ? mp.label : ''}
              </div>
            )
          })}
        </div>

        <div className="flex gap-0">
          {/* Day labels */}
          <div className="flex flex-col mr-1" style={{ gap: GAP }}>
            {DAY_LABELS.map((label, i) => (
              <div
                key={i}
                style={{ height: CELL, fontSize: 9 }}
                className="text-muted-foreground flex items-center"
              >
                {i % 2 === 1 ? label.slice(0, 3) : ''}
              </div>
            ))}
          </div>

          {/* Grid */}
          <div className="flex" style={{ gap: GAP }}>
            {weeks.map((week, col) => (
              <div key={col} className="flex flex-col" style={{ gap: GAP }}>
                {week.map(({ date, entry }) => {
                  const color = getColor(entry)
                  const hasAteWell = entry?.ateWell

                  return (
                    <div
                      key={date}
                      style={{
                        width: CELL,
                        height: CELL,
                        backgroundColor: color,
                        borderRadius: 2,
                        cursor: 'pointer',
                        border: hasAteWell ? '1.5px solid #f0c000' : '1px solid #21262d',
                        flexShrink: 0,
                        boxSizing: 'border-box',
                      }}
                      onClick={() => onDayClick(date)}
                      onMouseEnter={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect()
                        setTooltip({ date, x: rect.left, y: rect.top })
                      }}
                      onMouseLeave={() => setTooltip(null)}
                    />
                  )
                })}
              </div>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="flex gap-4 mt-3 text-xs text-muted-foreground items-center">
          <span className="flex items-center gap-1">
            <span style={{ width: 10, height: 10, background: COLORS.running, borderRadius: 2, display: 'inline-block' }} />
            Running
          </span>
          <span className="flex items-center gap-1">
            <span style={{ width: 10, height: 10, background: COLORS.weights, borderRadius: 2, display: 'inline-block' }} />
            Weights
          </span>
          <span className="flex items-center gap-1">
            <span style={{ width: 10, height: 10, background: COLORS.both, borderRadius: 2, display: 'inline-block' }} />
            Both
          </span>
          <span className="flex items-center gap-1">
            <span style={{ width: 10, height: 10, background: COLORS.empty, borderRadius: 2, border: '1.5px solid #f0c000', display: 'inline-block', boxSizing: 'border-box' }} />
            Ate well
          </span>
        </div>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 bg-popover text-popover-foreground border border-border text-xs rounded px-2 py-1 pointer-events-none"
          style={{ left: tooltip.x + 16, top: tooltip.y - 8 }}
        >
          {tooltip.date}
        </div>
      )}
    </div>
  )
}
