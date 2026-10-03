import React from 'react';
import { Link } from 'react-router-dom';
import { Users, BarChart2, CheckSquare, PlusCircle, Mic, LogOut, Video, Settings, LayoutDashboard, FileText, Bell, Search, Star, AlertCircle } from 'lucide-react';

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
          <Link to="#" className="nav-item active">
            <LayoutDashboard size={20} /> Dashboard
          </Link>
          <Link to="#" className="nav-item">
            <Video size={20} /> My Classes
          </Link>
          <Link to="#" className="nav-item">
            <BarChart2 size={20} /> Analytics
          </Link>
          <Link to="#" className="nav-item">
            <Users size={20} /> Students
          </Link>
          <Link to="#" className="nav-item">
            <FileText size={20} /> Assignments
          </Link>
          <Link to="#" className="nav-item">
            <Settings size={20} /> Settings
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
            <h2 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>Professor Dashboard</h2>
            <p style={{ color: 'var(--text-muted)' }}>Manage your classes, view AI insights, and track student performance.</p>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <div style={{ position: 'relative', width: '250px' }}>
              <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input type="text" className="form-control" placeholder="Search..." style={{ paddingLeft: '40px', borderRadius: '20px', padding: '8px 16px 8px 40px' }} />
            </div>
            <Bell size={24} color="var(--text-light)" style={{ cursor: 'pointer' }} />
            <button className="btn-primary animate-pulse-glow" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Mic size={18} /> Record Lecture
            </button>
          </div>
        </header>

        {/* Stats Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '32px' }}>
          <div className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <p style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: 600 }}>Total Students</p>
              <Users size={18} color="var(--primary-color)" />
            </div>
            <h3 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>342</h3>
            <p style={{ fontSize: '12px', color: 'var(--success)' }}>+12 this semester</p>
          </div>
          <div className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <p style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: 600 }}>Avg. Attendance</p>
              <CheckSquare size={18} color="var(--success)" />
            </div>
            <h3 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>94%</h3>
            <p style={{ fontSize: '12px', color: 'var(--success)' }}>+2% from last week</p>
          </div>
          <div className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <p style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: 600 }}>Avg. AI Understanding</p>
              <Star size={18} color="var(--warning)" />
            </div>
            <h3 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>8.2/10</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Based on AI Q&A metrics</p>
          </div>
          <div className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <p style={{ color: 'var(--text-muted)', fontSize: '13px', fontWeight: 600 }}>Unanswered Questions</p>
              <AlertCircle size={18} color="var(--secondary-color)" />
            </div>
            <h3 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px' }}>14</h3>
            <p style={{ fontSize: '12px', color: 'var(--secondary-color)' }}>Needs your review</p>
          </div>
        </div>

        {/* Content Row */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* AI Insights Panel */}
            <div className="card" style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.05), rgba(236,72,153,0.05))', border: '1px solid rgba(99,102,241,0.2)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <BarChart2 size={20} color="var(--primary-color)" /> AI Lecture Insights
                </h3>
              </div>
              <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '16px' }}>
                Based on your last lecture "Introduction to Neural Networks", here is what the AI analyzed from student questions:
              </p>
              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ flex: 1, background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px' }}>
                  <h4 style={{ fontSize: '14px', marginBottom: '8px', color: 'var(--warning)' }}>Most Confusing Topic</h4>
                  <p style={{ fontSize: '13px' }}>Gradient Descent & Learning Rates (45 students asked about this).</p>
                </div>
                <div style={{ flex: 1, background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px' }}>
                  <h4 style={{ fontSize: '14px', marginBottom: '8px', color: 'var(--success)' }}>Most Understood</h4>
                  <p style={{ fontSize: '13px' }}>Activation Functions (High confidence in quiz responses).</p>
                </div>
              </div>
            </div>

            {/* Class List */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '18px' }}>Recent Recordings</h3>
                <Link to="#" style={{ color: 'var(--primary-color)', fontSize: '14px', textDecoration: 'none' }}>View Archive</Link>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                <thead>
                  <tr style={{ color: 'var(--text-muted)', textAlign: 'left', borderBottom: '1px solid var(--glass-border)' }}>
                    <th style={{ paddingBottom: '12px', fontWeight: 500 }}>Lecture Name</th>
                    <th style={{ paddingBottom: '12px', fontWeight: 500 }}>Date</th>
                    <th style={{ paddingBottom: '12px', fontWeight: 500 }}>Views</th>
                    <th style={{ paddingBottom: '12px', fontWeight: 500 }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { title: 'Lecture 12: Neural Networks', date: 'Today', views: 85, status: 'AI Processing' },
                    { title: 'Lecture 11: Support Vector Machines', date: 'Oct 1', views: 320, status: 'Ready' },
                    { title: 'Lecture 10: Decision Trees', date: 'Sep 28', views: 341, status: 'Ready' },
                  ].map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={{ padding: '16px 0', display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '6px', background: 'var(--glass-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Video size={16} color="var(--primary-color)" />
                        </div>
                        {row.title}
                      </td>
                      <td style={{ padding: '16px 0', color: 'var(--text-muted)' }}>{row.date}</td>
                      <td style={{ padding: '16px 0' }}>{row.views}</td>
                      <td style={{ padding: '16px 0' }}>
                        <span style={{ fontSize: '12px', padding: '4px 10px', borderRadius: '12px', background: row.status === 'Ready' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)', color: row.status === 'Ready' ? 'var(--success)' : 'var(--warning)' }}>
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Column: Quick Actions & Live Polls */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="card">
              <h3 style={{ fontSize: '18px', marginBottom: '16px' }}>Quick Actions</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <button className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', textAlign: 'left', border: '1px solid var(--primary-color)', background: 'rgba(99,102,241,0.05)' }}>
                  <PlusCircle size={20} color="var(--primary-color)" />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--primary-color)' }}>Create Live Poll</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Engage students instantly</div>
                  </div>
                </button>
                <button className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', textAlign: 'left' }}>
                  <CheckSquare size={20} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '14px' }}>Generate Quiz</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>AI creates quiz from lecture</div>
                  </div>
                </button>
                <button className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', textAlign: 'left' }}>
                  <FileText size={20} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '14px' }}>Export Attendance</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Download CSV report</div>
                  </div>
                </button>
              </div>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '18px', marginBottom: '16px' }}>Student Performance</h3>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>Top students flagged for extra help this week.</p>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {[
                  { name: 'Sarah Jenkins', issue: 'Missed 2 classes', color: 'var(--warning)' },
                  { name: 'Michael Chen', issue: 'Failed Quiz #3', color: 'var(--secondary-color)' }
                ].map((student, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <span style={{ fontSize: '14px', fontWeight: 600 }}>{student.name.charAt(0)}</span>
                    </div>
                    <div>
                      <h4 style={{ fontSize: '14px' }}>{student.name}</h4>
                      <p style={{ fontSize: '12px', color: student.color }}>{student.issue}</p>
                    </div>
                    <button className="btn-secondary" style={{ padding: '4px 8px', fontSize: '12px', marginLeft: 'auto' }}>Message</button>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default TeacherDashboard;
