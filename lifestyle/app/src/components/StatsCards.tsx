import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Stats } from '@/lib/api'

interface StatsCardsProps {
  stats: Stats | null
}

const statDefs = [
  { key: 'totalMiles', label: 'Total Miles', icon: '🏃', fmt: (v: number) => v.toFixed(1) },
  { key: 'runningDays', label: 'Running Days', icon: '📅', fmt: (v: number) => String(v) },
  { key: 'weightDays', label: 'Weight Days', icon: '🏋️', fmt: (v: number) => String(v) },
  { key: 'streak', label: 'Current Streak', icon: '🔥', fmt: (v: number) => `${v}d` },
  { key: 'bestStreak', label: 'Best Streak', icon: '⭐', fmt: (v: number) => `${v}d` },
  { key: 'avgMilesPerRun', label: 'Avg Miles/Run', icon: '📏', fmt: (v: number) => v.toFixed(2) },
  { key: 'avgCalories', label: 'Avg Calories', icon: '🍽️', fmt: (v: number) => `${v} cal` },
  { key: 'avgProtein', label: 'Avg Protein', icon: '💪', fmt: (v: number) => `${v}g` },
] as const

export function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {statDefs.map(({ key, label, icon, fmt }) => (
        <Card key={key} className="bg-card border-border">
          <CardHeader className="pb-1 pt-3 px-4">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              {icon} {label}
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3">
            <div className="text-2xl font-bold text-foreground">
              {stats ? fmt(stats[key] as number) : '—'}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
