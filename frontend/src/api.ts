// Client for the Campus Customs FastAPI backend (see backend/main.py).
// Requests go through the Vite proxy, so paths are relative.

export interface SizeStock {
  size: string
  quantity: number
  in_stock: boolean
}

export interface ProductSummary {
  product_id: string
  name: string
  garment_type: string
  category: string
  short_description: string
  colors: string[]
  price: number
  image_url: string
  total_stock: number
}

export interface ProductDetail extends ProductSummary {
  description: string
  search_tags: string[]
  sizes: SizeStock[]
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

/** Where the shopper is, so "do you have this in pink?" has a referent. */
export interface PageContext {
  path: string
  product_id: string | null
}

export interface StoredMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  products: ProductSummary[]
  created_at: string
}

export interface ChatResponse {
  reply: string
  /** Full product cards, already resolved against the catalogue by the backend. */
  products: ProductSummary[]
  /** Short label for what the agent searched, used as the results heading. */
  search_query: string | null
  /** The query to re-run on the Products page. Server-verified to return results. */
  search_terms: string | null
  /** How many products matched in total, when more exist than were returned. */
  total_matches: number | null
}

export interface PublicUser {
  id: number
  first_name: string | null
  last_name: string | null
  name: string
  email: string
  created_at: string
}

export interface AuthResponse {
  token: string
  user: PublicUser
}

export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

const TOKEN_KEY = 'campus-customs-token'

/** Header the backend uses to hand back a token with a reset expiry. */
const REFRESH_HEADER = 'X-Refreshed-Token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

/**
 * Sliding expiry: every authenticated response carries a fresh token, so an
 * active session never hits the short TTL while an idle one still does.
 */
function captureRefreshedToken(response: Response) {
  const refreshed = response.headers.get(REFRESH_HEADER)
  if (refreshed) {
    setToken(refreshed)
  }
}

/** Carries the server's message so forms can show why a request failed. */
export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function postJSON<T>(url: string, body: unknown, token?: string): Promise<T> {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  })

  captureRefreshedToken(response)

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      payload && typeof payload.detail === 'string'
        ? payload.detail
        : 'Something went wrong. Please try again.'
    throw new ApiError(detail, response.status)
  }
  return payload as T
}

export function login(email: string, password: string) {
  return postJSON<AuthResponse>('/api/auth/login', { email, password })
}

export function register(input: RegisterInput) {
  return postJSON<AuthResponse>('/api/auth/register', input)
}

export async function fetchCurrentUser(token: string): Promise<PublicUser> {
  const response = await fetch('/api/auth/me', {
    headers: { Authorization: `Bearer ${token}` },
  })

  captureRefreshedToken(response)

  if (!response.ok) {
    throw new ApiError('Session is no longer valid.', response.status)
  }
  return response.json() as Promise<PublicUser>
}

async function getJSON<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Request to ${url} failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export function fetchProducts(
  options: { search?: string; category?: string; size?: string; color?: string } = {},
) {
  const params = new URLSearchParams()
  if (options.search) params.set('search', options.search)
  if (options.category && options.category !== 'All') params.set('category', options.category)
  if (options.size && options.size !== 'Any') params.set('size', options.size)
  if (options.color) params.set('color', options.color)
  const query = params.toString()
  return getJSON<ProductSummary[]>(`/api/products${query ? `?${query}` : ''}`)
}

/** In-stock products from the same category, closest in price. */
export function fetchRelatedProducts(productId: string) {
  return getJSON<ProductSummary[]>(`/api/products/${encodeURIComponent(productId)}/related`)
}

export function fetchProduct(productId: string) {
  return getJSON<ProductDetail>(`/api/products/${encodeURIComponent(productId)}`)
}

export function fetchCategories() {
  return getJSON<string[]>('/api/categories')
}

export function formatPrice(price: number) {
  return `$${price.toFixed(2)}`
}

// Stub for now - the backend returns a canned reply until the agent is wired up.
export async function sendChatMessage(
  message: string,
  history: ChatTurn[] = [],
  page?: PageContext,
): Promise<ChatResponse> {
  // The token is optional: guests can chat, they just get nothing saved.
  const token = getToken()
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message, history, page }),
  })

  captureRefreshedToken(response)

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const detail =
      payload && typeof payload.detail === 'string'
        ? payload.detail
        : `Chat request failed (${response.status})`
    throw new ApiError(detail, response.status)
  }
  return payload as ChatResponse
}

/** A signed-in shopper's saved conversation. Empty for guests. */
export async function fetchChatHistory(): Promise<StoredMessage[]> {
  const token = getToken()
  if (!token) return []

  const response = await fetch('/api/chat/history', {
    headers: { Authorization: `Bearer ${token}` },
  })
  captureRefreshedToken(response)
  if (!response.ok) return []

  const payload = (await response.json()) as { messages: StoredMessage[] }
  return payload.messages ?? []
}

export async function clearChatHistory(): Promise<void> {
  const token = getToken()
  if (!token) return
  const response = await fetch('/api/chat/history', {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  captureRefreshedToken(response)
}
