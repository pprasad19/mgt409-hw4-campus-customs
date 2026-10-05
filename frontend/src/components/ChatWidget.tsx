import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useMatch } from 'react-router-dom'
import {
  fetchChatHistory,
  formatPrice,
  sendChatMessage,
  type ChatTurn,
  type PageContext,
  type ProductSummary,
} from '../api'
import { useAuth } from '../auth/useAuth'
import { useChatResults } from '../chat/useChatResults'

interface Message {
  role: 'user' | 'assistant'
  content: string
  products?: ProductSummary[]
}

const GREETING: Message = {
  role: 'assistant',
  content:
    "Hi! I'm the Campus Customs shop assistant. Ask me about hoodies, crewnecks, sizes, or anything in the catalogue.",
}

/** One-tap openers, so a shopper never faces an empty box wondering what to type. */
const QUICK_REPLIES = [
  'What hoodies do you have?',
  'Anything for my residential college?',
  'What is in stock in XL?',
  'Something warm for a game',
]

/** Turns sent back to the agent so follow-ups resolve. Excludes the greeting. */
function toHistory(messages: Message[]): ChatTurn[] {
  return messages.slice(1).map((m) => ({ role: m.role, content: m.content }))
}

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [draft, setDraft] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const { show: showResults } = useChatResults()
  const { user } = useAuth()
  const location = useLocation()

  // Which product page the shopper is on, if any. This is what gives "this"
  // a referent when they ask "do you have this in pink?".
  const productMatch = useMatch('/products/:productId')
  const page: PageContext = {
    path: location.pathname,
    product_id: productMatch?.params.productId ?? null,
  }

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isOpen])

  // Signing in reloads the saved conversation; signing out drops back to a
  // fresh greeting so the next person at the keyboard sees nothing personal.
  useEffect(() => {
    if (!user) {
      setMessages([GREETING])
      return
    }

    let cancelled = false
    setIsLoadingHistory(true)
    fetchChatHistory()
      .then((stored) => {
        if (cancelled || stored.length === 0) return
        setMessages([
          GREETING,
          ...stored.map((m) => ({
            role: m.role,
            content: m.content,
            products: m.products,
          })),
        ])
      })
      .catch(() => {
        /* A failed history load should not stop someone chatting. */
      })
      .finally(() => {
        if (!cancelled) setIsLoadingHistory(false)
      })

    return () => {
      cancelled = true
    }
  }, [user])

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    await send(draft)
  }

  async function send(raw: string) {
    const text = raw.trim()
    if (!text || isSending) return

    const history = toHistory(messages)
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setDraft('')
    setIsSending(true)

    try {
      const response = await sendChatMessage(text, history, page)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.reply, products: response.products },
      ])
      // Hand the matches to the page, which renders them as full product cards.
      showResults(
        response.products,
        response.search_query,
        response.total_matches,
        response.search_terms,
      )
    } catch (caught) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            caught instanceof Error
              ? caught.message
              : "I couldn't reach the shop right now. Please try again.",
        },
      ])
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="chat-dock">
      {isOpen && (
        <section className="chat-panel" aria-label="Shop assistant">
          <header className="chat-header">
            <span className="chat-avatar" aria-hidden="true">CC</span>
            <div className="chat-header-text">
              <strong>Shop Assistant</strong>
              <span className="chat-status">
                {user
                  ? `Signed in as ${user.first_name?.trim() || user.name} - chat saved`
                  : 'Sign in to save your chat'}
              </span>
            </div>
            <button
              type="button"
              className="chat-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              &times;
            </button>
          </header>

          <div className="chat-messages" ref={scrollRef}>
            {isLoadingHistory && (
              <div className="chat-bubble chat-bubble-assistant chat-loading">
                Loading your conversation...
              </div>
            )}

            {messages.map((message, index) => (
              <div key={index} className="chat-entry">
                <div className={`chat-bubble chat-bubble-${message.role}`}>{message.content}</div>

                {message.products && message.products.length > 0 && (
                  <div className="chat-cards">
                    {message.products.map((product) => (
                      <Link
                        key={product.product_id}
                        to={`/products/${product.product_id}`}
                        className="chat-card"
                        onClick={() => setIsOpen(false)}
                      >
                        <img src={product.image_url} alt={product.name} loading="lazy" />
                        <div className="chat-card-body">
                          <span className="chat-card-name">{product.name}</span>
                          <span className="chat-card-price">{formatPrice(product.price)}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {isSending && (
              <div className="chat-bubble chat-bubble-assistant chat-typing" aria-label="Searching">
                <span /><span /><span />
              </div>
            )}
          </div>

          {messages.length <= 1 && !isSending && (
            <div className="chat-quick-replies">
              {QUICK_REPLIES.map((reply) => (
                <button key={reply} type="button" className="quick-reply" onClick={() => send(reply)}>
                  {reply}
                </button>
              ))}
            </div>
          )}

          <form className="chat-input-row" onSubmit={handleSubmit}>
            <input
              type="text"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about a product..."
              aria-label="Message the shop assistant"
            />
            <button type="submit" className="btn btn-primary" disabled={!draft.trim() || isSending}>
              Send
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        className="chat-launcher"
        onClick={() => setIsOpen((open) => !open)}
        aria-expanded={isOpen}
      >
        {isOpen ? 'Close chat' : 'Chat with us'}
      </button>
    </div>
  )
}
