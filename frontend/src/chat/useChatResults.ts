import { useContext } from 'react'
import { ChatResultsContext, type ChatResultsState } from './ChatResultsContext'

export function useChatResults(): ChatResultsState {
  const context = useContext(ChatResultsContext)
  if (!context) {
    throw new Error('useChatResults must be used inside a ChatResultsProvider')
  }
  return context
}
