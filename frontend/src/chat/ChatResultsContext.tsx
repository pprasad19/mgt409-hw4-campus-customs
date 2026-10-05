import { createContext, useCallback, useMemo, useState } from 'react'
import type { ProductSummary } from '../api'

/**
 * The products the shop agent most recently surfaced.
 *
 * The chat panel writes here; the results band on the page reads from here.
 * Keeping it in context rather than inside ChatWidget is what lets the cards
 * render in the page itself and survive navigation - a shopper can open a
 * product, come back, and the results they asked for are still there.
 */
export interface ChatResultsState {
  products: ProductSummary[]
  /** Short label for what was searched, e.g. "hoodies". */
  query: string | null
  /** Total number of matches, when the agent showed only some of them. */
  totalMatches: number | null
  /** Query to re-run on the Products page for the rest of the matches. */
  searchTerms: string | null
  /** Bumped on every new result set, so the band knows to scroll into view. */
  revision: number
  show: (
    products: ProductSummary[],
    query: string | null,
    totalMatches: number | null,
    searchTerms: string | null,
  ) => void
  clear: () => void
}

export const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function ChatResultsProvider({ children }: { children: React.ReactNode }) {
  const [products, setProducts] = useState<ProductSummary[]>([])
  const [query, setQuery] = useState<string | null>(null)
  const [totalMatches, setTotalMatches] = useState<number | null>(null)
  const [searchTerms, setSearchTerms] = useState<string | null>(null)
  const [revision, setRevision] = useState(0)

  const show = useCallback(
    (
      next: ProductSummary[],
      nextQuery: string | null,
      nextTotal: number | null,
      nextTerms: string | null,
    ) => {
      // An empty result set should not wipe what the shopper is already looking
      // at - a follow-up question that returns nothing leaves the band alone.
      if (next.length === 0) return
      setProducts(next)
      setQuery(nextQuery)
      setTotalMatches(nextTotal)
      setSearchTerms(nextTerms)
      setRevision((n) => n + 1)
    },
    [],
  )

  const clear = useCallback(() => {
    setProducts([])
    setQuery(null)
    setTotalMatches(null)
    setSearchTerms(null)
  }, [])

  const value = useMemo(
    () => ({ products, query, totalMatches, searchTerms, revision, show, clear }),
    [products, query, totalMatches, searchTerms, revision, show, clear],
  )

  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}
