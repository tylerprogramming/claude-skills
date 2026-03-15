import { useEffect, useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { getActivityDay, type ActivityEntry } from '@/lib/api'
import { formatDate } from '@/lib/utils'

interface DayModalProps {
  date: string | null
  onClose: () => void
}

export function DayModal({ date, onClose }: DayModalProps) {
  const [entry, setEntry] = useState<ActivityEntry | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!date) return
    setLoading(true)
    getActivityDay(date)
      .then((e) => setEntry(e))
      .finally(() => setLoading(false))
  }, [date])

  if (!date) return null

  const hasActivity = entry && (entry.weights || entry.running || entry.ateWell)

  // Parse note segments separated by " | "
  const segments = entry?.notes
    ? entry.notes.split(' | ').filter(Boolean)
    : []

  const nutritionSeg = segments.find((s) => s.toLowerCase().startsWith('nutrition:'))
  const activitySegs = segments.filter((s) => !s.toLowerCase().startsWith('nutrition:'))

  return (
    <Dialog open={!!date} onOpenChange={(open: boolean) => !open && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{formatDate(date)}</DialogTitle>
        </DialogHeader>

        {loading && <p className="text-sm text-muted-foreground">Loading...</p>}

        {!loading && !hasActivity && (
          <p className="text-sm text-muted-foreground">No activity logged for this day.</p>
        )}

        {!loading && hasActivity && (
          <div className="space-y-4">
            {/* Badges */}
            <div className="flex gap-2 flex-wrap">
              {entry.running && (
                <Badge style={{ backgroundColor: '#388bfd', color: 'white' }}>🏃 Running</Badge>
              )}
              {entry.weights && (
                <Badge style={{ backgroundColor: '#da3633', color: 'white' }}>🏋️ Weights</Badge>
              )}
              {entry.ateWell && (
                <Badge style={{ backgroundColor: '#f0c000', color: '#0d1117' }}>🥗 Ate Well</Badge>
              )}
            </div>

            {/* Activity notes */}
            {activitySegs.length > 0 && (
              <div className="space-y-1">
                {activitySegs.map((seg, i) => (
                  <p key={i} className="text-sm text-foreground">{seg}</p>
                ))}
              </div>
            )}

            {/* Nutrition */}
            {(nutritionSeg || entry.calories != null) && (
              <div className="rounded-md bg-muted p-3 space-y-1">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Nutrition</p>
                {entry.calories != null && (
                  <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-sm">
                    <span className="text-muted-foreground">Calories</span>
                    <span>{entry.calories} cal</span>
                    {entry.protein != null && (
                      <>
                        <span className="text-muted-foreground">Protein</span>
                        <span>{entry.protein}g</span>
                      </>
                    )}
                    {entry.fat != null && (
                      <>
                        <span className="text-muted-foreground">Fat</span>
                        <span>{entry.fat}g</span>
                      </>
                    )}
                    {entry.carbs != null && (
                      <>
                        <span className="text-muted-foreground">Carbs</span>
                        <span>{entry.carbs}g</span>
                      </>
                    )}
                  </div>
                )}
                {nutritionSeg && !entry.calories && (
                  <p className="text-sm text-foreground">{nutritionSeg}</p>
                )}
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
