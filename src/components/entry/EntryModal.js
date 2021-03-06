import React, { Component } from 'react'
import { Modal } from 'semantic-ui-react'
import { PropTypes } from 'prop-types'
import EntryForm from './EntryForm'
import { openEntryModal, closeEntryModal } from '../../actions'
import { connect } from 'react-redux'

export class EntryModal extends Component {
  static propTypes = {
    open: PropTypes.bool.isRequired,
    initialModalValues: PropTypes.object,
    closeEntryModal: PropTypes.func,
    trigger: PropTypes.element
  }

  constructor (props) {
    super(props)
    this.handleClose = this.handleClose.bind(this)
  }

  handleClose () {
    this.props.closeEntryModal()
  }

  render () {
    // Test for null/undefined or empty object
    const isNewEntry = !this.props.initialModalValues || Object.keys(this.props.initialModalValues).length === 0

    const actionText = isNewEntry ? 'Create' : 'Edit'
    return (
      <Modal open={this.props.open} onClose={this.handleClose} trigger={this.props.trigger}>
        <Modal.Header content={`${actionText} an Entry`} />
        <Modal.Content>
          <EntryForm
            initialValues={this.props.initialModalValues}
            isNewEntry={isNewEntry} />
        </Modal.Content>
      </Modal>
    )
  }
}

function mapStateToProps (state) {
  return {
    open: state.entry.entryModalOpen,
    initialModalValues: state.entry.initialModalValues
  }
}

export default connect(mapStateToProps, { openEntryModal, closeEntryModal })(EntryModal)
