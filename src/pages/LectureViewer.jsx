import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft, HardDrive, Clock, Calendar, BookOpen, Target, 
  Lightbulb, Sigma, HelpCircle, MonitorPlay, ChevronDown, ChevronUp, PlayCircle, Search, AlertTriangle, CheckCircle2
} from 'lucide-react';
import { mockLectureMemory } from '../mocks/lectureMemory';

export default function LectureViewer() {
  const { lectureId } = useParams();
  const [lecture, setLecture] = useState(mockLectureMemory);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!lectureId || lectureId === 'lecture_demo_20261006_01') {
      setLecture(mockLectureMemory);
      return;
    }
    setIsLoading(true);
    fetch(`http://localhost:8000/api/lectures/${lectureId}`)
      .then(res => {
        if (!res.ok) throw new Error('Not found');
        return res.json();
      })
      .then(data => {
        // Merge with defaults to prevent any undefined rendering issues
        setLecture({
          ...mockLectureMemory,
          ...data,
          timeline_events: data.timeline_events || [],
          concepts: data.concepts || [],
          definitions: data.definitions || [],
          equations: data.equations || [],
          important_points: data.important_points || [],
          revision_questions: data.revision_questions || [],
        });
      })
      .catch(err => {
        console.warn('Could not load lecture from backend, falling back to mock:', err);
        setLecture(mockLectureMemory);
      })
      .finally(() => setIsLoading(false));
  }, [lectureId]);


  const [activeQuestion, setActiveQuestion] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h > 0 ? h + 'h ' : ''}${m}m ${s > 0 ? s + 's' : ''}`;
  };

  const formatTimelineTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleSeek = (timestamp) => {
    console.log(`Seeking to timestamp: ${timestamp}s`);
    // Placeholder for video player seek functionality
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-darker)', color: 'var(--text-primary)', paddingBottom: '4rem' }}>
      
      {/* Navigation & Header */}
      <nav style={{ padding: '1.5rem 2rem', borderBottom: '1px solid var(--border-color)', background: 'rgba(2, 6, 23, 0.8)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 50 }}>
        <div style={{ maxWidth: '1440px', margin: '0 auto', display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <Link to="/dashboard/student" style={{ color: 'var(--text-secondary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px', transition: 'color 0.2s' }} className="hover:text-white">
            <ArrowLeft size={20} />
            Back
          </Link>
          <div style={{ height: '24px', width: '1px', background: 'var(--border-color)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255, 255, 255, 0.05)', padding: '4px 12px', borderRadius: '20px', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--accent)' }}>DEMO MODE</span>
          </div>
        </div>
      </nav>

      <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '3rem 2rem', display: 'grid', gridTemplateColumns: '300px 1fr', gap: '3rem' }}>
        
        {/* Left Sidebar: Timeline */}
        <aside style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ position: 'sticky', top: '100px' }}>
            <div style={{ marginBottom: '2rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Timeline</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Key moments from the lecture</p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
              {lecture.timeline_events.map((evt, i) => (
                <div key={i} style={{ display: 'flex', gap: '16px', position: 'relative', cursor: 'pointer' }} onClick={() => handleSeek(evt.timestamp)} className="timeline-item">
                  {i !== lecture.timeline_events.length - 1 && (
                    <div style={{ position: 'absolute', left: '15px', top: '32px', bottom: '-8px', width: '2px', background: 'var(--border-color)' }} />
                  )}
                  
                  <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1, marginTop: '2px', transition: 'all 0.2s' }} className="timeline-icon-container">
                    {evt.type === 'speech' && <PlayCircle size={14} color="var(--text-secondary)" />}
                    {evt.type === 'visual' && <MonitorPlay size={14} color="var(--success)" />}
                    {evt.type === 'equation' && <Sigma size={14} color="var(--accent)" />}
                    {evt.type === 'concept' && <Lightbulb size={14} color="#f59e0b" />}
                    {evt.type === 'multimodal' && <Target size={14} color="#ec4899" />}
                  </div>

                  <div style={{ paddingBottom: '24px', flex: 1, transition: 'transform 0.2s' }} className="timeline-content">
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{formatTimelineTime(evt.timestamp)}</span>
                      <span style={{ fontWeight: 500, fontSize: '0.95rem', color: 'var(--text-primary)' }}>{evt.label}</span>
                    </div>
                    {evt.details && <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>{evt.details}</p>}
                  </div>
                </div>
              ))}
            </div>
            
            <style>{`
              .timeline-item:hover .timeline-icon-container { background: rgba(255,255,255,0.1); border-color: var(--text-muted); }
              .timeline-item:hover .timeline-content { transform: translateX(4px); }
            `}</style>
          </div>
        </aside>

        {/* Right Content: Lecture Memory */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
          
          {/* Header Section */}
          <header className="glass-panel" style={{ padding: '3rem', position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: 0, right: 0, width: '300px', height: '300px', background: 'radial-gradient(circle, rgba(94, 106, 210, 0.15) 0%, rgba(0,0,0,0) 70%)', transform: 'translate(30%, -30%)' }} />
            
            <div style={{ display: 'flex', gap: '12px', marginBottom: '1.5rem' }}>
              <span style={{ background: 'rgba(255,255,255,0.05)', padding: '6px 12px', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)' }}>{lecture.subject}</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--success)', background: 'rgba(52, 211, 153, 0.1)', padding: '6px 12px', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 500 }}>
                <HardDrive size={14} /> Stored locally
              </span>
            </div>

            <h1 style={{ fontSize: '3rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: '1.5rem', lineHeight: 1.1 }}>{lecture.title}</h1>
            
            <div style={{ display: 'flex', gap: '2rem', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Calendar size={16} /> {lecture.date}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Clock size={16} /> {formatTime(lecture.duration)}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>ID: {lecture.session_id}</div>
            </div>
          </header>

          {/* Search UI */}
          <section>
            <div className="glass-panel" style={{ padding: '1.5rem 2rem', display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(255,255,255,0.05)' }}>
              <Search size={20} color="var(--text-muted)" />
              <input 
                type="text" 
                placeholder="Ask your lecture memory... (e.g. 'What did the teacher say about Ohm's law?')" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', color: 'var(--text-primary)', fontSize: '1rem' }}
              />
              {searchQuery && (
                <button onClick={() => setIsSearching(true)} style={{ background: 'var(--accent)', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: 500 }}>
                  Search
                </button>
              )}
            </div>
            
            {isSearching && (
              <div className="glass-panel" style={{ marginTop: '1rem', padding: '2rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent)', marginBottom: '1rem' }}>
                  <Search size={16} /> <span>Searching lecture memory... (Demo)</span>
                </div>
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>Found relevance: Ohm's Law</span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Score: 0.95 | Timestamp: 10:32</span>
                  </div>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0 }}>
                    The teacher explained Ohm's Law (I=V/R) and wrote it on the board.
                  </p>
                </div>
              </div>
            )}
          </section>

          {/* Overview Section */}
          <section>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BookOpen size={20} color="var(--accent)" /> Overview
            </h2>
            <div className="glass-panel" style={{ padding: '2rem', background: 'rgba(255,255,255,0.02)' }}>
              <p style={{ fontSize: '1.1rem', lineHeight: 1.7, color: 'var(--text-secondary)', margin: 0 }}>{lecture.overview}</p>
            </div>
          </section>

          {/* Concepts Section */}
          <section>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Lightbulb size={20} color="#f59e0b" /> Key Concepts
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
              {lecture.concepts.map(concept => (
                <div key={concept.id} className="glass-panel hover-lift concept-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', transition: 'transform 0.2s, box-shadow 0.2s', cursor: 'pointer' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>{concept.name}</h3>
                    <button onClick={(e) => { e.stopPropagation(); handleSeek(concept.timestamp); }} style={{ background: 'transparent', border: 'none', color: 'var(--accent)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}>
                      <PlayCircle size={14} /> {formatTimelineTime(concept.timestamp)}
                    </button>
                  </div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6, margin: 0 }}>{concept.explanation}</p>
                  
                  {concept.evidence && (
                    <div style={{ marginTop: '0.5rem', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: 600 }}>Why GyanDrishti Trusts This</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {concept.evidence.speech && <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>🎤 <strong>Speech:</strong> "{concept.evidence.speech}"</div>}
                        {concept.evidence.visual && <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>👁 <strong>Visual:</strong> "{concept.evidence.visual}"</div>}
                        <div style={{ marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 600, color: concept.evidence.status === 'CONFLICT' ? 'var(--danger)' : 'var(--success)' }}>
                          {concept.evidence.status === 'CONFLICT' ? <AlertTriangle size={12} /> : <CheckCircle2 size={12} />}
                          {concept.evidence.status}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Equations Section */}
          <section>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sigma size={20} color="#ec4899" /> Equations
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {lecture.equations.map((eq, i) => (
                <div key={i} className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
                    <div style={{ flex: 1 }}>
                      <h4 style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)', marginBottom: '1rem' }}>{eq.name}</h4>
                      <div style={{ fontSize: '2rem', fontFamily: 'var(--font-mono)', fontWeight: 300, letterSpacing: '0.05em', color: 'var(--text-primary)' }}>
                        {eq.representation}
                      </div>
                    </div>
                    <div style={{ flex: 1, borderLeft: '1px solid var(--border-color)', paddingLeft: '2rem' }}>
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6, margin: 0 }}>{eq.explanation}</p>
                      <button onClick={() => handleSeek(eq.timestamp)} style={{ marginTop: '1rem', background: 'transparent', border: 'none', color: 'var(--accent)', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', fontFamily: 'var(--font-mono)', padding: 0 }}>
                        <PlayCircle size={14} /> Jump to {formatTimelineTime(eq.timestamp)}
                      </button>
                    </div>
                  </div>
                  
                  {eq.evidence && (
                    <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: 600 }}>Evidence Explanation</div>
                      <div style={{ display: 'flex', gap: '2rem' }}>
                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {eq.evidence.speech && <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>🎤 <strong>Speech:</strong> "{eq.evidence.speech}"</div>}
                          {eq.evidence.visual && <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>👁 <strong>Visual:</strong> "{eq.evidence.visual}"</div>}
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'center' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.85rem', fontWeight: 600, color: eq.evidence.status === 'CONFLICT' ? 'var(--danger)' : 'var(--success)' }}>
                            {eq.evidence.status === 'CONFLICT' ? <AlertTriangle size={14} /> : <CheckCircle2 size={14} />}
                            {eq.evidence.status}
                          </div>
                          {eq.evidence.temporal_match && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Temporal Match: {eq.evidence.temporal_match}</div>}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Visual References */}
          <section>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MonitorPlay size={20} color="var(--success)" /> Visual Evidence
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
              {lecture.visual_references.map((vr, i) => (
                <div key={i} className="glass-panel" style={{ overflow: 'hidden', padding: 0 }}>
                  <div style={{ height: '160px', background: 'rgba(255,255,255,0.03)', display: 'flex', alignItems: 'center', justifyContent: 'center', borderBottom: '1px solid var(--border-color)' }}>
                    {/* Placeholder for actual frame image */}
                    <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                      <MonitorPlay size={32} style={{ marginBottom: '8px', opacity: 0.5 }} />
                      <div style={{ fontSize: '0.85rem' }}>{vr.local_frame_reference}</div>
                    </div>
                  </div>
                  <div style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-primary)' }}>{vr.event_type}</span>
                      <span style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>{formatTimelineTime(vr.timestamp)}</span>
                    </div>
                    {vr.description && <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0 }}>{vr.description}</p>}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Revision Questions */}
          <section>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <HelpCircle size={20} color="#8b5cf6" /> Revision
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {lecture.revision_questions.map((q, i) => (
                <div key={i} className="glass-panel" style={{ padding: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', cursor: 'pointer' }} onClick={() => setActiveQuestion(activeQuestion === i ? null : i)}>
                    <h4 style={{ fontSize: '1.05rem', fontWeight: 500, color: 'var(--text-primary)', margin: 0, paddingRight: '2rem', lineHeight: 1.5 }}>
                      {q.question}
                    </h4>
                    <div style={{ color: 'var(--text-muted)' }}>
                      {activeQuestion === i ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                    </div>
                  </div>
                  
                  <AnimatePresence>
                    {activeQuestion === i && (
                      <motion.div 
                        initial={{ opacity: 0, height: 0 }} 
                        animate={{ opacity: 1, height: 'auto' }} 
                        exit={{ opacity: 0, height: 0 }}
                        style={{ overflow: 'hidden' }}
                      >
                        <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
                          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6, margin: 0, marginBottom: '1rem' }}>{q.answer}</p>
                          <button onClick={() => handleSeek(q.timestamp)} style={{ background: 'transparent', border: 'none', color: 'var(--accent)', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', fontFamily: 'var(--font-mono)', padding: 0 }}>
                            <PlayCircle size={14} /> Review concept at {formatTimelineTime(q.timestamp)}
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </section>

        </div>
      </main>

      <style>{`
        .hover-lift:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.2); }
      `}</style>
    </div>
  );
}
