import React, { Component } from 'react'
import { connect } from 'react-redux'
import { Field, reduxForm } from 'redux-form'
import { registerUser, clearAuthError } from '../../actions'
import { Redirect } from 'react-router'
import { PropTypes } from 'prop-types'
import { Button, Form } from 'semantic-ui-react'
import SemanticReduxFormField from '../form/SemanticReduxFormField'
import ErrorMessage from '../ErrorMessage'

const form = reduxForm({
  form: 'register',
  validate
})

function validate (formProps) {
  const errors = {}

  if (!formProps.email) {
    errors.email = 'Please enter an email'
  } else if (!/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i.test(formProps.email)) {
    errors.email = 'Invalid email address.'
  }

  if (!formProps.password) {
    errors.password = 'Please enter a password'
  } else if (formProps.password.length < 8) {
    errors.password = 'Your password must be 8 characters or longer.'
  }

  if (!formProps.name) {
    errors.name = 'Please enter your name'
  }

  return errors
}

class RegisterForm extends Component {
  constructor (props) {
    super(props)
    this.handleFormSubmit = this.handleFormSubmit.bind(this)
  }

  componentWillMount () {
    this.props.clearAuthError()
  }

  handleFormSubmit (formProps) {
    this.props.registerUser(formProps)
  }

  renderAlert () {
    if (!this.props.errorMessage) {
      return null
    }

    return (
      <ErrorMessage message={this.props.errorMessage} />
    )
  }

  render () {
    const { handleSubmit } = this.props

    return (
      <Form warning error onSubmit={handleSubmit(this.handleFormSubmit)}>
        {this.props.authenticated ? (<Redirect push to='/dashboard' />) : null}
        <Form.Field>
          <label>Email</label>
          <Field component={SemanticReduxFormField} as={Form.Input} name='email' placeholder='Email' />
        </Form.Field>
        <Form.Field>
          <label>Name</label>
          <Field component={SemanticReduxFormField} as={Form.Input} name='name' placeholder='What should we call you?' />
        </Form.Field>
        <Form.Field>
          <label>Password</label>
          <Field component={SemanticReduxFormField} as={Form.Input} name='password' placeholder='Password' type='password' />
        </Form.Field>
        <Button type='submit' positive>Sign Up</Button>
        {this.renderAlert()}
      </Form>
    )
  }
}

RegisterForm.propTypes = {
  registerUser: PropTypes.func.isRequired,
  clearAuthError: PropTypes.func.isRequired,
  errorMessage: PropTypes.string,
  handleSubmit: PropTypes.func.isRequired,
  authenticated: PropTypes.bool
}

function mapStateToProps (state) {
  return {
    errorMessage: state.auth.error,
    message: state.auth.message,
    authenticated: state.auth.authenticated
  }
}

export default connect(mapStateToProps, { registerUser, clearAuthError })(form(RegisterForm))
