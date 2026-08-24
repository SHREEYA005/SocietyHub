import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  if (!user) return null

  const base = user.role === 'admin' ? '/admin' : '/dashboard'

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to={base}>SocietyHub</Link>
      </div>
      <div className="navbar-links">
        {user.role === 'resident' && (
          <>
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/complaints/new">Raise Complaint</Link>
            <Link to="/notices">Notices</Link>
          </>
        )}
        {user.role === 'admin' && (
          <>
            <Link to="/admin">Dashboard</Link>
            <Link to="/admin/complaints">Complaints</Link>
            <Link to="/admin/notices">Notices</Link>
          </>
        )}
      </div>
      <div className="navbar-user">
        <span className="navbar-username">{user.name}</span>
        <button className="btn btn-ghost" onClick={handleLogout}>Log out</button>
      </div>
    </nav>
  )
}
