import type { PropsWithChildren } from 'react'

interface TabButtonProps extends PropsWithChildren {
  active: boolean
  onClick: () => void
}

export function TabButton({ active, onClick, children }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`rounded-xl border px-4 py-2 text-sm font-medium transition ${
        active
          ? 'border-blue-400 bg-blue-600/20 text-blue-100 shadow-lg shadow-blue-900/30'
          : 'border-slate-700 bg-slate-900/80 text-slate-300 hover:border-slate-500 hover:text-white'
      }`}
    >
      {children}
    </button>
  )
}
