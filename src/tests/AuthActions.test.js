import configureStore from 'redux-mock-store'
import thunk from 'redux-thunk'
import * as actions from '../actions/AuthActions'
import * as types from '../actions/types'
import nock from 'nock'
import jwt from 'jwt-simple'
import httpAdapter from 'axios/lib/adapters/http'
import axios from 'axios'
import expect from 'expect'
import Cookie from 'universal-cookie'

const middlewares = [ thunk ]
const mockStore = configureStore(middlewares)

axios.defaults.adapter = httpAdapter

jest.mock('universal-cookie')

describe('Async Auth Actions', () => {
  afterEach(() => {
    nock.cleanAll()
  })

  it('creates AUTH_USER and sets cookie after loginUser is done', () => {
    const login = {
      email: 'foo@bar.baz',
      password: 'test'
    }
    const authObject = {foo: 'bar'}
    const fakeToken = jwt.encode(authObject, 'secret')

    nock('http://localhost:5000/')
      .post('/login')
      .reply(200, { status: 'success', auth_token: fakeToken })

    const expectedActions = [
      { type: types.AUTH_USER, payload: authObject }
    ]
    const store = mockStore({})

    return store.dispatch(actions.loginUser(login))
      .then(() => { // return of async actions
        expect(store.getActions()).toEqual(expectedActions)
        expect(Cookie.mock.instances.length).toEqual(1)
        expect(Cookie.mock.instances[0].set.mock.calls).toContain(['token', fakeToken, { path: '/' }])
      })
  })

  it('creates AUTH_USER and sets cookie after registerUser is done', () => {
    const login = {
      email: 'foo@bar.baz',
      password: 'test'
    }
    const authObject = {foo: 'bar'}
    const fakeToken = jwt.encode(authObject, 'secret')

    nock('http://localhost:5000/')
      .post('/register')
      .reply(200, { status: 'success', auth_token: fakeToken })

    const expectedActions = [
      { type: types.AUTH_USER, payload: authObject }
    ]
    const store = mockStore({})

    return store.dispatch(actions.registerUser(login))
      .then(() => { // return of async actions
        expect(store.getActions()).toEqual(expectedActions)
        expect(Cookie.mock.instances.length).toEqual(1)
        expect(Cookie.mock.instances[0].set.mock.calls).toContain(['token', fakeToken, { path: '/' }])
      })
  })
})