import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import ScrollToTop from './data/scrollTop.jsx'
import { AuthProvider } from './data/authcontext.jsx'
import App from './App.jsx'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ScrollToTop/>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
)