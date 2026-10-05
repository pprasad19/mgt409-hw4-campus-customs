import { Outlet, Route, Routes } from 'react-router-dom'
import ChatResultsBand from './components/ChatResultsBand'
import ChatWidget from './components/ChatWidget'
import CommandPalette from './components/CommandPalette'
import NavBar from './components/NavBar'
import Ticker from './components/Ticker'
import About from './pages/About'
import CreateAccount from './pages/CreateAccount'
import Home from './pages/Home'
import LogIn from './pages/LogIn'
import NotFound from './pages/NotFound'
import ProductDetailPage from './pages/ProductDetail'
import Products from './pages/Products'

function Layout() {
  return (
    <div className="app-shell">
      <Ticker />
      <NavBar />
      <main className="app-main">
        {/* Products the agent found, shown on whatever page the shopper is on. */}
        <ChatResultsBand />
        <Outlet />
      </main>
      <footer className="app-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <span className="footer-mark">Campus Customs</span>
            <span className="footer-note">New Haven, Connecticut</span>
          </div>
          <span className="footer-note">Printed on campus, worn everywhere</span>
        </div>
      </footer>
      <ChatWidget />
      <CommandPalette />
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/products" element={<Products />} />
        <Route path="/products/:productId" element={<ProductDetailPage />} />
        <Route path="/about" element={<About />} />
        <Route path="/login" element={<LogIn />} />
        <Route path="/create-account" element={<CreateAccount />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
