import { useState } from 'react'
import type { Exercise, ActivityEntry } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface StrengthChartsProps {
  exercises: Exercise[]
  activity: ActivityEntry[]
}

interface RunPoint {
  date: string
  totalSeconds: number
  label: string
  pace: string
}

interface DataPoint {
  date: string
  maxWeight: number
  label: string
}

function getDataPoints(exercise: Exercise): DataPoint[] {
  return exercise.entries
    .map((entry) => {
      const weights = entry.sets.map((s) => s.weight ?? 0).filter((w) => w > 0)
      const maxWeight = weights.length > 0 ? Math.max(...weights) : 0
      const totalReps = entry.sets.reduce((sum, s) => sum + (s.reps ?? 1), 0)
      return {
        date: entry.date,
        maxWeight,
        label: maxWeight > 0 ? `${maxWeight} lbs` : `${totalReps} reps`,
      }
    })
    .sort((a, b) => a.date.localeCompare(b.date))
}

function MiniChart({ points }: { points: DataPoint[] }) {
  if (points.length < 2) {
    return (
      <div className="h-16 flex items-center justify-center text-xs text-muted-foreground">
        {points.length === 1 ? `${points[0].label} on ${points[0].date}` : 'No data'}
      </div>
    )
  }

  const values = points.map((p) => p.maxWeight)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  const W = 200
  const H = 60
  const PAD = 6

  const toX = (i: number) => PAD + (i / (points.length - 1)) * (W - PAD * 2)
  const toY = (v: number) => H - PAD - ((v - min) / range) * (H - PAD * 2)

  const latest = points[points.length - 1]
  const prev = points[points.length - 2]
  const trend = latest.maxWeight >= prev.maxWeight ? '↑' : '↓'
  const trendColor = latest.maxWeight >= prev.maxWeight ? '#3fb950' : '#f85149'

  return (
    <div className="space-y-1">
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} className="overflow-visible">
        <polyline
          points={points.map((p, i) => `${toX(i)},${toY(p.maxWeight)}`).join(' ')}
          fill="none"
          stroke="#388bfd"
          strokeWidth="1.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {points.map((p, i) => (
          <circle key={i} cx={toX(i)} cy={toY(p.maxWeight)} r={3} fill="#388bfd" />
        ))}
      </svg>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{points[0].date.slice(5)}</span>
        <span style={{ color: trendColor }}>
          {trend} {latest.label}
        </span>
        <span>{latest.date.slice(5)}</span>
      </div>
    </div>
  )
}

function parseTimeToSeconds(t: string): number {
  const parts = t.split(':').map(Number)
  return parts.length === 2 ? parts[0] * 60 + parts[1] : parts[0] * 3600 + parts[1] * 60 + parts[2]
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function getRunPoints(activity: ActivityEntry[], targetMiles: number, tolerance = 0.08): RunPoint[] {
  const points: RunPoint[] = []
  for (const entry of activity) {
    if (!entry.running || !entry.notes) continue
    const match = entry.notes.match(/[\d.]+\s*mi,\s*(\d+:\d+),\s*([\d'"\/]+mi\s*pace)/)
    if (!match) continue
    const distMatch = entry.notes.match(/([\d.]+)\s*mi,/)
    if (!distMatch) continue
    const dist = parseFloat(distMatch[1])
    if (Math.abs(dist - targetMiles) > tolerance) continue
    const seconds = parseTimeToSeconds(match[1])
    points.push({ date: entry.date, totalSeconds: seconds, label: formatTime(seconds), pace: match[2] })
  }
  return points.sort((a, b) => a.date.localeCompare(b.date))
}

function RunChart({ points }: { points: RunPoint[] }) {
  const [hovered, setHovered] = useState<number | null>(null)

  if (points.length === 0) return <div className="h-24 flex items-center justify-center text-xs text-muted-foreground">No data</div>
  if (points.length === 1) return <div className="h-24 flex items-center justify-center text-xs text-muted-foreground">{points[0].label} on {points[0].date.slice(5)}</div>

  const W = 260
  const H = 90
  const PAD_L = 36  // left padding for Y axis labels
  const PAD_R = 8
  const PAD_T = 12
  const PAD_B = 20  // bottom padding for X axis labels

  const seconds = points.map((p) => p.totalSeconds)
  const minS = Math.min(...seconds)
  const maxS = Math.max(...seconds)
  const range = maxS - minS || 10

  // Add a bit of padding to the range so dots aren't right at edge
  const paddedMin = minS - range * 0.15
  const paddedMax = maxS + range * 0.15
  const paddedRange = paddedMax - paddedMin

  const toX = (i: number) => PAD_L + (i / (points.length - 1)) * (W - PAD_L - PAD_R)
  // Invert: lower seconds = higher on chart = better
  const toY = (s: number) => PAD_T + ((paddedMax - s) / paddedRange) * (H - PAD_T - PAD_B)

  const latest = points[points.length - 1]
  const prev = points[points.length - 2]
  const improved = latest.totalSeconds <= prev.totalSeconds
  const trendColor = improved ? '#3fb950' : '#f85149'

  // Y axis labels: show min and max times
  const yLabels = [minS, maxS]

  return (
    <div className="relative">
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} className="overflow-visible">
        {/* Y axis gridlines + labels */}
        {yLabels.map((s) => {
          const y = toY(s)
          return (
            <g key={s}>
              <line x1={PAD_L} y1={y} x2={W - PAD_R} y2={y} stroke="#21262d" strokeWidth="1" strokeDasharray="3 3" />
              <text x={PAD_L - 4} y={y + 4} textAnchor="end" fontSize="8" fill="#6e7681">{formatTime(s)}</text>
            </g>
          )
        })}

        {/* Line */}
        <polyline
          points={points.map((p, i) => `${toX(i)},${toY(p.totalSeconds)}`).join(' ')}
          fill="none"
          stroke="#388bfd"
          strokeWidth="1.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {/* Dots + hover targets */}
        {points.map((p, i) => {
          const cx = toX(i)
          const cy = toY(p.totalSeconds)
          const isHovered = hovered === i
          return (
            <g key={i}>
              <circle cx={cx} cy={cy} r={isHovered ? 5 : 3.5} fill={isHovered ? '#58a6ff' : '#388bfd'} style={{ transition: 'r 0.1s' }} />
              {/* Invisible larger hit area */}
              <circle
                cx={cx} cy={cy} r={10}
                fill="transparent"
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
                style={{ cursor: 'crosshair' }}
              />
            </g>
          )
        })}

        {/* X axis date labels — first and last */}
        <text x={toX(0)} y={H - 2} textAnchor="middle" fontSize="8" fill="#6e7681">{points[0].date.slice(5)}</text>
        <text x={toX(points.length - 1)} y={H - 2} textAnchor="middle" fontSize="8" fill="#6e7681">{points[points.length - 1].date.slice(5)}</text>
      </svg>

      {/* Hover tooltip */}
      {hovered !== null && (() => {
        const p = points[hovered]
        const xPct = ((toX(hovered)) / W) * 100
        const yPct = ((toY(p.totalSeconds)) / H) * 100
        const alignRight = xPct > 60
        return (
          <div
            className="absolute pointer-events-none z-10 bg-[#1c2128] border border-[#30363d] rounded px-2 py-1 text-xs text-[#c9d1d9] whitespace-nowrap shadow-lg"
            style={{
              left: alignRight ? undefined : `${xPct}%`,
              right: alignRight ? `${100 - xPct}%` : undefined,
              top: `${Math.max(0, yPct - 20)}%`,
              transform: alignRight ? 'translateX(8px)' : 'translateX(-50%)',
            }}
          >
            <div className="font-semibold">{p.label}</div>
            <div className="text-[#8b949e]">{p.date.slice(5)} · {p.pace}</div>
          </div>
        )
      })()}

      {/* Trend + best */}
      <div className="flex justify-between text-xs mt-1">
        <span className="text-muted-foreground">Best: <span className="text-[#c9d1d9]">{formatTime(Math.min(...seconds))}</span></span>
        <span style={{ color: trendColor }}>{improved ? '↑ faster' : '↓ slower'} last run</span>
      </div>
    </div>
  )
}

function RunningCards({ activity }: { activity: ActivityEntry[] }) {
  const runs3K = getRunPoints(activity, 1.86)
  const runs5K = getRunPoints(activity, 3.11)

  const cards = [
    { label: '3K Race Times', points: runs3K, subtitle: '~1.86 mi' },
    { label: '5K Race Times', points: runs5K, subtitle: '~3.11 mi' },
  ].filter((c) => c.points.length > 0)

  if (cards.length === 0) return null

  return (
    <>
      {cards.map((c) => (
        <Card key={c.label} className="bg-card border-border">
          <CardHeader className="pb-1 pt-3 px-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              🏃 {c.label}
              <span className="text-xs text-muted-foreground font-normal">{c.subtitle}</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3">
            <RunChart points={c.points} />
          </CardContent>
        </Card>
      ))}
    </>
  )
}

export function StrengthCharts({ exercises, activity }: StrengthChartsProps) {
  if (exercises.length === 0) {
    return <p className="text-sm text-muted-foreground">No strength data yet.</p>
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <RunningCards activity={activity} />
      {exercises
        .filter((ex) => ex.entries.length > 0)
        .map((ex) => {
          const points = getDataPoints(ex)
          return (
            <Card key={ex.slug} className="bg-card border-border">
              <CardHeader className="pb-1 pt-3 px-4">
                <CardTitle className="text-sm font-medium">{ex.name}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 pb-3">
                <MiniChart points={points} />
              </CardContent>
            </Card>
          )
        })}
    </div>
  )
}
