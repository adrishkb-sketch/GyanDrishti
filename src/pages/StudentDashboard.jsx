import React from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, MessageSquare, PlayCircle, Clock, Search, LogOut } from 'lucide-react';

const StudentDashboard = () => {
  return (
    <div className="dashboard-layout fade-in">
      {/* Sidebar */}
      <div className="sidebar">
        <Link to="/" style={{ textDecoration: 'none', color: 'white', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: 800 }}>
            Lecture<span className="gradient-text">AI</span>
          </h2>
        </Link>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
          <Link to="#" className="nav-item active">
            <BookOpen size={20} /> My Courses
          </Link>
          <Link to="#" className="nav-item">
            <PlayCircle size={20} /> Recorded Lectures
          </Link>
          <Link to="#" className="nav-item">
            <MessageSquare size={20} /> AI Q&A
          </Link>
          <Link to="#" className="nav-item">
            <Clock size={20} /> History
          </Link>
        </nav>

        <Link to="/login" className="nav-item" style={{ color: 'var(--secondary-color)' }}>
          <LogOut size={20} /> Logout
        </Link>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
          <div>
            <h2 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>Hello, Alex! 👋</h2>
            <p style={{ color: 'var(--text-muted)' }}>Ready to learn something new today?</p>
          </div>
          
          <div style={{ position: 'relative', width: '300px' }}>
            <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input type="text" className="form-control" placeholder="Search lectures, topics..." style={{ paddingLeft: '40px', borderRadius: '20px' }} />
          </div>
        </header>

        <h3 style={{ fontSize: '20px', marginBottom: '16px' }}>Recent AI Lectures</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px', marginBottom: '40px' }}>
          {[1, 2, 3].map((item) => (
            <div key={item} className="card" style={{ padding: '0', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <div style={{ height: '160px', background: 'linear-gradient(45deg, #1e293b, #334155)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <PlayCircle size={48} color="rgba(255,255,255,0.5)" />
              </div>
              <div style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--primary-color)', fontWeight: 600 }}>Computer Science</span>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Oct 3, 2026</span>
                </div>
                <h4 style={{ fontSize: '18px', marginBottom: '8px' }}>Machine Learning Basics {item}</h4>
                <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '16px' }}>Prof. Smith discusses neural networks and datasets.</p>
                
                <button className="btn-secondary" style={{ width: '100%', padding: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
                  <MessageSquare size={16} /> Ask AI
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="card" style={{ display: 'flex', gap: '24px' }}>
          <div style={{ flex: 1 }}>
            <h3 style={{ fontSize: '20px', marginBottom: '8px' }}>Ask AI Assistant</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '16px' }}>Have a question about a recent lecture? Our AI is here to help clarify concepts.</p>
            <div style={{ display: 'flex', gap: '12px' }}>
              <input type="text" className="form-control" placeholder="E.g., Explain backpropagation in simple terms..." />
              <button className="btn-primary" style={{ padding: '12px 24px' }}>Ask</button>
            </div>
          </div>
          <div style={{ width: '120px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <MessageSquare size={64} color="var(--primary-color)" style={{ opacity: 0.5 }} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;
