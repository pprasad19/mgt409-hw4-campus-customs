import { useEffect, useState } from 'react'

type Theme = 'light' | 'dark'
const KEY = 'campus-customs-theme'

/** Honour the visitor's own system setting until they choose for themselves. */
function initialTheme(): Theme {
  const saved = localStorage.getItem(KEY)
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      return initialTheme()
    } catch {
      return 'light'
    }
  })

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try {
      localStorage.setItem(KEY, theme)
    } catch {
      /* Private browsing can refuse storage; the theme still applies. */
    }
  }, [theme])

  const next = theme === 'light' ? 'dark' : 'light'

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={() => setTheme(next)}
      aria-label={`Switch to ${next} mode`}
      title={`Switch to ${next} mode`}
    >
      {theme === 'light' ? '◐' : '◑'}
    </button>
  )
}
