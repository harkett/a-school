import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { crashed: false }
  }

  static getDerivedStateFromError() {
    return { crashed: true }
  }

  render() {
    if (!this.state.crashed) return this.props.children

    return (
      <div style={{
        minHeight: '100dvh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f0f4f8',
        padding: '32px 16px',
        textAlign: 'center',
      }}>
        <img src="/Logo_aSchool.png" alt="aSchool" style={{ width: 120, marginBottom: 24 }} />
        <p style={{ fontSize: '16px', color: '#374151', marginBottom: 8, fontWeight: 500 }}>
          Une erreur inattendue s'est produite.
        </p>
        <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: 24 }}>
          Rechargez l'application pour continuer.
        </p>
        <button
          onClick={() => window.location.reload()}
          title="Recharger l'application"
          style={{
            background: '#6b001d',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            padding: '10px 24px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Recharger l'application
        </button>
      </div>
    )
  }
}
