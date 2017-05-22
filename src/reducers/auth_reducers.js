import { AUTH_USER,
         UNAUTH_USER,
         AUTH_ERROR,
         LOAD_ENTRIES } from '../actions/types'

const INITIAL_STATE = { error: '', message: '', entries: [], authenticated: false, user: {} }

export default function (state = INITIAL_STATE, action) {
  switch (action.type) {
    case AUTH_USER:
      return { ...state, error: '', message: '', authenticated: true, user: action.payload }
    case UNAUTH_USER:
      return { ...state, authenticated: false, user: {} }
    case AUTH_ERROR:
      return { ...state, error: action.payload }
    case LOAD_ENTRIES:
      return { ...state, entries: action.payload }
  }

  return state
}
