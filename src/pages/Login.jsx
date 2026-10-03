import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { UserCircle, GraduationCap, ArrowRight } from 'lucide-react';

const Login = () => {
  const [role, setRole] = useState('student');
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    if (role === 'student') {
      navigate('/dashboard/student');
    } else {
      navigate('/dashboard/teacher');
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      position: 'relative'
    }}>
      <div style={{
          position: 'absolute',
          top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '600px', height: '600px',
          background: 'var(--primary-color)',
          filter: 'blur(200px)', opacity: 0.2, zIndex: 0
        }} />

      <div className="glass-panel fade-in" style={{ 
        width: '100%', 
        maxWidth: '420px', 
        padding: '40px', 
        zIndex: 1,
        textAlign: 'center'
      }}>
        <Link to="/" style={{ textDecoration: 'none', color: 'white', display: 'inline-block', marginBottom: '32px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 800 }}>
            Lecture<span className="gradient-text">AI</span>
          </h2>
        </Link>
        
        <h3 style={{ fontSize: '28px', marginBottom: '8px' }}>Welcome Back</h3>
        <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>Sign in to continue to your dashboard</p>

        <div style={{ display: 'flex', gap: '12px', marginBottom: '32px' }}>
          <button 
            onClick={() => setRole('student')}
            style={{
              flex: 1,
              padding: '12px',
              borderRadius: '8px',
              background: role === 'student' ? 'rgba(99,102,241,0.2)' : 'transparent',
              border: role === 'student' ? '1px solid var(--primary-color)' : '1px solid var(--glass-border)',
              color: 'white',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.3s'
            }}
          >
            <GraduationCap size={24} color={role === 'student' ? 'var(--primary-color)' : 'var(--text-muted)'} />
            <span style={{ fontSize: '14px', fontWeight: 500 }}>Student</span>
          </button>
          
          <button 
            onClick={() => setRole('teacher')}
            style={{
              flex: 1,
              padding: '12px',
              borderRadius: '8px',
              background: role === 'teacher' ? 'rgba(236,72,153,0.2)' : 'transparent',
              border: role === 'teacher' ? '1px solid var(--secondary-color)' : '1px solid var(--glass-border)',
              color: 'white',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.3s'
            }}
          >
            <UserCircle size={24} color={role === 'teacher' ? 'var(--secondary-color)' : 'var(--text-muted)'} />
            <span style={{ fontSize: '14px', fontWeight: 500 }}>Teacher</span>
          </button>
        </div>

        <form onSubmit={handleLogin} style={{ textAlign: 'left' }}>
          <div className="form-group">
            <label>Email Address</label>
            <input type="email" className="form-control" placeholder="john@example.com" required />
          </div>
          <div className="form-group" style={{ marginBottom: '32px' }}>
            <label>Password</label>
            <input type="password" className="form-control" placeholder="••••••••" required />
          </div>
          
          <button type="submit" className="btn-primary" style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
            Sign In <ArrowRight size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
