import React from 'react';
import { Link } from 'react-router-dom';
import { Users, BarChart2, CheckSquare, PlusCircle, Mic, LogOut, Video } from 'lucide-react';

const TeacherDashboard = () => {
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
          <Link to="#" className="nav-item">
            <Video size={20} /> My Classes
          </Link>
          <Link to="#" className="nav-item active">
            <BarChart2 size={20} /> Analytics
          </Link>
          <Link to="#" className="nav-item">
            <Users size={20} /> Attendance
          </Link>
          <Link to="#" className="nav-item">
            <CheckSquare size={20} /> Polls & Quizzes
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
            <h2 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>Dashboard</h2>
            <p style={{ color: 'var(--text-muted)' }}>Manage your classes and view student insights.</p>
          </div>
          
          <button className="btn-primary animate-pulse-glow" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Mic size={18} /> Start New Lecture
          </button>
        </header>

        {/* Stats Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px', marginBottom: '32px' }}>
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(99,102,241,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary-color)' }}>
              <Users size={24} />
            </div>
            <div>
              <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '4px' }}>Avg. Attendance</p>
              <h3 style={{ fontSize: '24px', fontWeight: 700 }}>92%</h3>
            </div>
          </div>
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(16,185,129,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--success)' }}>
              <CheckSquare size={24} />
            </div>
            <div>
              <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '4px' }}>Poll Completion</p>
              <h3 style={{ fontSize: '24px', fontWeight: 700 }}>85%</h3>
            </div>
          </div>
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(236,72,153,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--secondary-color)' }}>
              <BarChart2 size={24} />
            </div>
            <div>
              <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '4px' }}>Student Understanding</p>
              <h3 style={{ fontSize: '24px', fontWeight: 700 }}>Great</h3>
            </div>
          </div>
        </div>

        {/* Content Row */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          
          {/* Class List */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h3 style={{ fontSize: '20px' }}>Recent Lectures</h3>
              <Link to="#" style={{ color: 'var(--primary-color)', fontSize: '14px', textDecoration: 'none' }}>View All</Link>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {[
                { title: 'Machine Learning Basics', date: 'Today, 10:00 AM', status: 'Processing AI Notes' },
                { title: 'Data Structures: Trees', date: 'Yesterday', status: 'Completed' },
                { title: 'Introduction to Algorithms', date: 'Oct 1, 2026', status: 'Completed' },
              ].map((lecture, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'var(--glass-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Video size={20} color="var(--primary-color)" />
                    </div>
                    <div>
                      <h4 style={{ fontSize: '16px', marginBottom: '4px' }}>{lecture.title}</h4>
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{lecture.date}</p>
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '12px', padding: '4px 12px', borderRadius: '12px', background: lecture.status === 'Completed' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)', color: lecture.status === 'Completed' ? 'var(--success)' : 'var(--warning)' }}>
                      {lecture.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '20px', marginBottom: '8px' }}>Quick Actions</h3>
            
            <button className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', textAlign: 'left', border: '1px solid var(--primary-color)', background: 'rgba(99,102,241,0.05)' }}>
              <PlusCircle size={20} color="var(--primary-color)" />
              <div>
                <div style={{ fontWeight: 600, color: 'var(--primary-color)' }}>Create a Poll</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Check student understanding</div>
              </div>
            </button>

            <button className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', textAlign: 'left' }}>
              <Users size={20} />
              <div>
                <div style={{ fontWeight: 600 }}>Download Attendance</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>CSV format for current week</div>
              </div>
            </button>

            <button className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', textAlign: 'left' }}>
              <CheckSquare size={20} />
              <div>
                <div style={{ fontWeight: 600 }}>Review Questions</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>5 unanswered student queries</div>
              </div>
            </button>
          </div>

        </div>
      </div>
    </div>
  );
};

export default TeacherDashboard;
