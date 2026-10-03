import React from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, MessageSquare, PlayCircle, Clock, Search, LogOut, TrendingUp, Calendar, Bell, ChevronRight, Award } from 'lucide-react';

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
            <BookOpen size={20} /> Dashboard
          </Link>
          <Link to="#" className="nav-item">
            <PlayCircle size={20} /> My Courses
          </Link>
          <Link to="#" className="nav-item">
            <MessageSquare size={20} /> Ask AI
          </Link>
          <Link to="#" className="nav-item">
            <TrendingUp size={20} /> Performance
          </Link>
          <Link to="#" className="nav-item">
            <Calendar size={20} /> Schedule
          </Link>
        </nav>

        <div className="card" style={{ padding: '16px', background: 'rgba(99,102,241,0.1)', border: '1px solid var(--primary-color)', marginBottom: '16px' }}>
          <h4 style={{ fontSize: '14px', color: 'white', marginBottom: '8px' }}>Pro Plan Active</h4>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>You have unlimited AI questions left for this month.</p>
        </div>

        <Link to="/login" className="nav-item" style={{ color: 'var(--secondary-color)' }}>
          <LogOut size={20} /> Logout
        </Link>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
          <div>
            <h2 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>Welcome back, Alex! 👋</h2>
            <p style={{ color: 'var(--text-muted)' }}>You have 2 pending assignments and 1 upcoming lecture.</p>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            <div style={{ position: 'relative', width: '300px' }}>
              <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input type="text" className="form-control" placeholder="Search lectures, topics..." style={{ paddingLeft: '40px', borderRadius: '20px' }} />
            </div>
            <div style={{ position: 'relative', cursor: 'pointer' }}>
              <Bell size={24} color="var(--text-light)" />
              <div style={{ position: 'absolute', top: '-2px', right: '-2px', width: '10px', height: '10px', background: 'var(--secondary-color)', borderRadius: '50%', border: '2px solid var(--bg-darker)' }}></div>
            </div>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(45deg, var(--primary-color), var(--secondary-color))', cursor: 'pointer' }}></div>
          </div>
        </header>

        {/* Stats Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '32px' }}>
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '20px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(99,102,241,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary-color)' }}>
              <BookOpen size={24} />
            </div>
            <div>
              <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '4px' }}>Courses in Progress</p>
              <h3 style={{ fontSize: '24px', fontWeight: 700 }}>4</h3>
            </div>
          </div>
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '20px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(16,185,129,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--success)' }}>
              <Award size={24} />
            </div>
            <div>
              <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '4px' }}>Average Score</p>
              <h3 style={{ fontSize: '24px', fontWeight: 700 }}>88%</h3>
            </div>
          </div>
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '20px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(236,72,153,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--secondary-color)' }}>
              <MessageSquare size={24} />
            </div>
            <div>
              <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '4px' }}>AI Questions Asked</p>
              <h3 style={{ fontSize: '24px', fontWeight: 700 }}>124</h3>
            </div>
          </div>
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '20px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(245,158,11,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--warning)' }}>
              <Clock size={24} />
            </div>
            <div>
              <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginBottom: '4px' }}>Hours Learned</p>
              <h3 style={{ fontSize: '24px', fontWeight: 700 }}>36h</h3>
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '32px' }}>
          {/* Left Column */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '20px' }}>Continue Learning</h3>
              <Link to="#" style={{ color: 'var(--primary-color)', fontSize: '14px', textDecoration: 'none', display: 'flex', alignItems: 'center' }}>
                View All <ChevronRight size={16} />
              </Link>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '40px' }}>
              {[
                { title: 'Machine Learning: Neural Networks', course: 'CS401 - Artificial Intelligence', progress: 75, date: 'Watched yesterday' },
                { title: 'Data Structures: Hash Maps', course: 'CS201 - Algorithms', progress: 30, date: 'Watched 2 days ago' }
              ].map((item, idx) => (
                <div key={idx} className="card" style={{ display: 'flex', gap: '20px', padding: '16px', alignItems: 'center' }}>
                  <div style={{ width: '120px', height: '80px', borderRadius: '8px', background: 'linear-gradient(45deg, #1e293b, #334155)', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                    <PlayCircle size={32} color="rgba(255,255,255,0.7)" />
                    <div style={{ position: 'absolute', bottom: 0, left: 0, height: '4px', background: 'rgba(255,255,255,0.2)', width: '100%', borderBottomLeftRadius: '8px', borderBottomRightRadius: '8px' }}>
                      <div style={{ width: `${item.progress}%`, height: '100%', background: 'var(--primary-color)', borderRadius: '4px' }}></div>
                    </div>
                  </div>
                  <div style={{ flex: 1 }}>
                    <span style={{ fontSize: '12px', color: 'var(--primary-color)', fontWeight: 600 }}>{item.course}</span>
                    <h4 style={{ fontSize: '16px', marginBottom: '4px', marginTop: '4px' }}>{item.title}</h4>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{item.date}</span>
                  </div>
                  <button className="btn-secondary" style={{ padding: '8px 16px', fontSize: '14px' }}>Resume</button>
                </div>
              ))}
            </div>

            <div className="card" style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.1), rgba(236,72,153,0.1))', border: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ display: 'flex', gap: '24px' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '20px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <MessageSquare size={20} color="var(--primary-color)" /> Ask AI Assistant
                  </h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '20px' }}>
                    Stuck on a concept? Ask the AI to summarize lectures, explain topics, or generate practice questions based on your courses.
                  </p>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <input type="text" className="form-control" placeholder="E.g., Explain backpropagation like I'm 5..." style={{ background: 'rgba(0,0,0,0.3)' }} />
                    <button className="btn-primary" style={{ padding: '12px 24px', whiteSpace: 'nowrap' }}>Ask AI</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div>
            <div className="card" style={{ marginBottom: '24px' }}>
              <h3 style={{ fontSize: '18px', marginBottom: '16px' }}>Upcoming Schedule</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {[
                  { title: 'Live Q&A: AI Ethics', time: 'Today, 2:00 PM', type: 'Live Session' },
                  { title: 'Midterm Assignment Due', time: 'Tomorrow, 11:59 PM', type: 'Deadline', isWarning: true },
                  { title: 'Algorithms Lecture', time: 'Friday, 10:00 AM', type: 'Lecture' }
                ].map((event, idx) => (
                  <div key={idx} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: event.isWarning ? 'var(--warning)' : 'var(--primary-color)', marginTop: '4px' }}></div>
                    <div>
                      <h4 style={{ fontSize: '14px', marginBottom: '2px' }}>{event.title}</h4>
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{event.time} • {event.type}</p>
                    </div>
                  </div>
                ))}
              </div>
              <button className="btn-secondary" style={{ width: '100%', marginTop: '20px', fontSize: '14px', padding: '8px' }}>View Full Calendar</button>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '18px', marginBottom: '16px' }}>Recent AI Interactions</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>You asked:</p>
                  <p style={{ fontSize: '14px' }}>"What is the time complexity of QuickSort?"</p>
                </div>
                <div style={{ padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>You asked:</p>
                  <p style={{ fontSize: '14px' }}>"Summarize the main points of Lecture 4."</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;
