import { useState } from 'react'
import type { NutritionItem } from '@/lib/api'
import { createNutritionItem, deleteNutritionItem } from '@/lib/api'

interface Props {
  items: NutritionItem[]
  onUpdate: () => void
}

const EMPTY: Omit<NutritionItem, 'id'> = {
  name: '',
  serving_size: '',
  calories: 0,
  protein: 0,
  fat: 0,
  carbs: 0,
  sodium: 0,
  fiber: 0,
  sugar: 0,
}

export function NutritionSection({ items, onUpdate }: Props) {
  const [search, setSearch] = useState('')
  const [adding, setAdding] = useState(false)
  const [form, setForm] = useState(EMPTY)

  const filtered = items.filter((i) =>
    i.name.toLowerCase().includes(search.toLowerCase())
  )

  const handleAdd = async () => {
    if (!form.name || !form.serving_size) return
    await createNutritionItem(form)
    setForm(EMPTY)
    setAdding(false)
    onUpdate()
  }

  const handleDelete = async (id: number) => {
    await deleteNutritionItem(id)
    onUpdate()
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search foods..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-1.5 text-sm text-[#c9d1d9] placeholder-[#484f58] focus:border-[#388bfd] focus:outline-none"
        />
        <button
          onClick={() => setAdding(!adding)}
          className="px-3 py-1.5 text-xs rounded-md bg-[#238636] text-white hover:bg-[#2ea043] transition-colors"
        >
          {adding ? 'Cancel' : '+ Add Food'}
        </button>
      </div>

      {adding && (
        <div className="rounded-lg border border-[#30363d] bg-[#161b22] p-4">
          <div className="grid grid-cols-2 gap-3 mb-3">
            <input
              placeholder="Food name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="col-span-2 bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-1.5 text-sm text-[#c9d1d9] placeholder-[#484f58] focus:border-[#388bfd] focus:outline-none"
            />
            <input
              placeholder="Serving size (e.g. 1 scoop, 32g)"
              value={form.serving_size}
              onChange={(e) => setForm({ ...form, serving_size: e.target.value })}
              className="col-span-2 bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-1.5 text-sm text-[#c9d1d9] placeholder-[#484f58] focus:border-[#388bfd] focus:outline-none"
            />
            {(['calories', 'protein', 'fat', 'carbs', 'sodium', 'fiber', 'sugar'] as const).map((field) => (
              <div key={field} className="flex flex-col gap-1">
                <label className="text-[10px] uppercase text-[#8b949e] tracking-wider">{field}</label>
                <input
                  type="number"
                  value={form[field] || ''}
                  onChange={(e) => setForm({ ...form, [field]: Number(e.target.value) || 0 })}
                  className="bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-1.5 text-sm text-[#c9d1d9] focus:border-[#388bfd] focus:outline-none"
                />
              </div>
            ))}
          </div>
          <button
            onClick={handleAdd}
            disabled={!form.name || !form.serving_size}
            className="w-full px-3 py-1.5 text-xs rounded-md bg-[#238636] text-white hover:bg-[#2ea043] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Save Food Item
          </button>
        </div>
      )}

      <div className="rounded-lg border border-[#30363d] bg-[#161b22] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#21262d] text-[#8b949e] text-xs uppercase tracking-wider">
              <th className="text-left px-4 py-2">Food</th>
              <th className="text-left px-2 py-2">Serving</th>
              <th className="text-right px-2 py-2">Cal</th>
              <th className="text-right px-2 py-2">Protein</th>
              <th className="text-right px-2 py-2">Fat</th>
              <th className="text-right px-2 py-2">Carbs</th>
              <th className="text-right px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-[#484f58] text-sm">
                  {search ? 'No matching foods' : 'No foods added yet'}
                </td>
              </tr>
            )}
            {filtered.map((item) => (
              <tr key={item.id} className="border-b border-[#21262d] hover:bg-[#1c2128] transition-colors">
                <td className="px-4 py-2 text-[#c9d1d9] font-medium">{item.name}</td>
                <td className="px-2 py-2 text-[#8b949e]">{item.serving_size}</td>
                <td className="px-2 py-2 text-right text-[#c9d1d9]">{item.calories}</td>
                <td className="px-2 py-2 text-right text-[#3fb950]">{item.protein}g</td>
                <td className="px-2 py-2 text-right text-[#d29922]">{item.fat}g</td>
                <td className="px-2 py-2 text-right text-[#388bfd]">{item.carbs}g</td>
                <td className="px-4 py-2 text-right">
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="text-[#484f58] hover:text-[#da3633] transition-colors text-xs"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-[10px] text-[#484f58]">
        {items.length} food{items.length !== 1 ? 's' : ''} in database
      </p>
    </div>
  )
}
