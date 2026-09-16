import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { initTelegram } from './telegram'

// Tell Telegram the Mini App is ready and let it expand to full height.
// No-op when running outside Telegram (e.g. a plain browser in dev).
initTelegram()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
