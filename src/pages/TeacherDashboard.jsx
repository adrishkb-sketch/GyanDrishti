import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Video, Monitor, Mic, ShieldAlert, ShieldCheck, Activity, Play, Square, Pause, HardDrive, AlertCircle, ChevronDown, CheckCircle2 } from 'lucide-react';
import * as api from '../api/video';

export default function TeacherDashboard() {
  const [status, setStatus] = useState('idle'); // idle, recording, paused, stopped, error
  const [devices, setDevices] = useState({ cameras: [], screens: [] });
  const [selectedCam, setSelectedCam] = useState(0);
  const [selectedScreen, setSelectedScreen] = useState(1);
  const [backendOffline, setBackendOffline] = useState(false);
  const [session, setSession] = useState(null);
  const [duration, setDuration] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [demoTime, setDemoTime] = useState(0);
  
  const pollInterval = useRef(null);

  useEffect(() => {
    fetchDevices();
    checkStatus();
    return () => clearInterval(pollInterval.current);
  }, []);

  const fetchDevices = async (demo = isDemoMode) => {
    if (demo) {
      setDevices({
        cameras: [{ id: 0, name: 'Demo Camera HD' }],
        screens: [{ id: 1, name: 'Demo Display (1920x1080)' }]
      });
      setSelectedCam(0);
      setSelectedScreen(1);
      setBackendOffline(false);
      return;
    }
    try {
      const data = await api.fetchDevices();
      setDevices(data);
      if (data.cameras.length > 0) setSelectedCam(data.cameras[0].id);
      if (data.screens.length > 0) setSelectedScreen(data.screens[0].id);
      setBackendOffline(false);
    } catch (e) {
      setBackendOffline(true);
      setErrorMessage(e.message || 'Failed to fetch devices');
    }
  };

  const checkStatus = async () => {
    if (isDemoMode) return;
    try {
      const data = await api.getSessionStatus();
      setBackendOffline(false);
      if (data.is_recording) {
        setStatus(data.is_paused ? 'paused' : 'recording');
        setSession(data);
        setDuration(data.duration);
        startPolling();
      } else if (data.session_id && status === 'recording') {
        setStatus('stopped');
        setSession(data);
        clearInterval(pollInterval.current);
      }
    } catch (e) {
      setBackendOffline(true);
      setErrorMessage(e.message || 'Failed to check status');
    }
  };

  const startPolling = () => {
    if (pollInterval.current) clearInterval(pollInterval.current);
    pollInterval.current = setInterval(async () => {
      try {
        const data = await api.getSessionStatus();
        if (data.is_recording) {
          setSession(data);
          setDuration(data.duration);
        } else {
          clearInterval(pollInterval.current);
        }
      } catch (e) {
        console.error("Polling error", e);
      }
    }, 1000);
  };

  const handleStart = async () => {
    if (isDemoMode) {
      setStatus('recording');
      setSession({ session_id: 'demo_session_2026', events: [] });
      setDuration(0);
      setDemoTime(0);
      if (pollInterval.current) clearInterval(pollInterval.current);
      pollInterval.current = setInterval(() => {
        setDemoTime(t => {
          const newTime = t + 1;
          setDuration(newTime);
          if (newTime % 5 === 0) { // Add a fake event every 5 seconds
            setSession(prev => ({
              ...prev,
              events: [...(prev.events || []), { timestamp: newTime, source: 'screen', type: 'keyframe', change_score: Math.random() }]
            }));
          }
          return newTime;
        });
      }, 1000);
      return;
    }
    try {
      const data = await api.startSession(selectedCam, selectedScreen);
      setStatus('recording');
      setSession({ session_id: data.session_id, events: [] });
      setDuration(0);
      startPolling();
    } catch (e) {
      setStatus('error');
      setErrorMessage(e.message || 'Failed to start recording. Please check camera/microphone permissions and ensure backend is running.');
    }
  };

  const handlePauseResume = async () => {
    try {
      if (status === 'recording') {
        await api.pauseSession();
        setStatus('paused');
      } else {
        await api.resumeSession();
        setStatus('recording');
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleStop = async () => {
    if (confirm("Stop this lecture?\n\nThe current recording will be finalized and stored locally on this device.")) {
      if (isDemoMode) {
        setStatus('stopped');
        clearInterval(pollInterval.current);
        return;
      }
      try {
        const data = await api.stopSession();
        setStatus('stopped');
        setSession(data);
        setDuration(data.duration);
        clearInterval(pollInterval.current);
      } catch (e) {
        console.error(e);
      }
    }
  };

  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h > 0 ? h + ':' : ''}${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  if (backendOffline && !isDemoMode) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', padding: '2rem' }}>
        <AlertCircle size={48} color="var(--danger)" style={{ marginBottom: '1rem' }} />
        <h2 style={{ fontSize: '1.5rem', fontWeight: 500, marginBottom: '0.5rem' }}>Unable to connect to the GyanDrishti Local Engine.</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', textAlign: 'center', maxWidth: '500px' }}>
          GyanDrishti is designed to be fully local. It seems the background engine is not currently running. Please start the local Python backend to begin capturing lectures.
        </p>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="capture-btn-secondary" onClick={() => fetchDevices(false)}>Retry Connection</button>
          <button className="capture-btn-primary" onClick={() => { setIsDemoMode(true); fetchDevices(true); }}>Enter Demo Mode</button>
        </div>
      </div>
    );
  }

  return (
    <div className="capture-dashboard" style={{ display: 'flex', minHeight: '100vh', padding: '2rem', gap: '2rem', maxWidth: '1440px', margin: '0 auto' }}>
      
      {/* Left Column: Controls & State */}
      <div style={{ flex: 2, display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 600, letterSpacing: '-0.02em' }}>GYAN DRISHTI</h1>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
              <ShieldCheck size={14} color="var(--success)" />
              <span>Local & Private</span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
             <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.9rem', color: isDemoMode ? 'var(--accent)' : 'var(--text-muted)' }}>
               <input type="checkbox" checked={isDemoMode} onChange={e => {
                 setIsDemoMode(e.target.checked);
                 if (e.target.checked) fetchDevices(true);
                 else { setStatus('idle'); fetchDevices(false); }
               }} style={{ cursor: 'pointer' }} />
               Demo Mode
             </label>
          </div>
        </header>

        <AnimatePresence mode="wait">
          {status === 'idle' && (
            <motion.div 
              key="setup"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="glass-panel" 
              style={{ padding: '3rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}
            >
              <div>
                <h2 style={{ fontSize: '2.5rem', fontWeight: 600, marginBottom: '0.5rem', letterSpacing: '-0.03em' }}>Lecture Capture</h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>Capture the lecture. Let GyanDrishti remember the important parts.</p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Video size={20} color="var(--text-muted)" />
                    <span style={{ fontWeight: 500 }}>Camera</span>
                  </div>
                  <select className="capture-select" value={selectedCam} onChange={e => setSelectedCam(Number(e.target.value))}>
                    {devices.cameras.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    {devices.cameras.length === 0 && <option disabled>No cameras found</option>}
                  </select>
                </div>
                
                <div style={{ height: '1px', background: 'var(--border-color)' }} />
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Monitor size={20} color="var(--text-muted)" />
                    <span style={{ fontWeight: 500 }}>Screen</span>
                  </div>
                  <select className="capture-select" value={selectedScreen} onChange={e => setSelectedScreen(Number(e.target.value))}>
                    {devices.screens.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                    {devices.screens.length === 0 && <option disabled>No screens found</option>}
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '1rem' }}>
                <button className="capture-btn-primary" style={{ padding: '1rem 2rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }} onClick={handleStart} disabled={devices.cameras.length === 0}>
                  <Play size={20} fill="currentColor" />
                  Start Lecture
                </button>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <HardDrive size={14} />
                  Stored locally on this device
                </div>
              </div>
            </motion.div>
          )}

          {(status === 'recording' || status === 'paused') && (
            <motion.div 
              key="recording"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="glass-panel"
              style={{ padding: '3rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '3rem', minHeight: '500px' }}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'rgba(248, 113, 113, 0.1)', color: 'var(--danger)', padding: '0.5rem 1rem', borderRadius: '20px', fontWeight: 600, fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                  <span className={`status-dot ${status === 'recording' ? 'error pulse' : 'inactive'}`} />
                  {status === 'recording' ? 'RECORDING' : 'PAUSED'}
                </div>
                <div style={{ fontSize: '4.5rem', fontWeight: 300, fontVariantNumeric: 'tabular-nums', fontFamily: 'var(--font-mono)', lineHeight: 1 }}>
                  {formatTime(duration)}
                </div>
                <div style={{ color: 'var(--text-muted)', marginTop: '1rem', fontFamily: 'var(--font-mono)' }}>
                  Session: {session?.session_id}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <button className="capture-btn-secondary" style={{ width: '120px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }} onClick={handlePauseResume}>
                  {status === 'recording' ? <><Pause size={18} /> Pause</> : <><Play size={18} /> Resume</>}
                </button>
                <button className="capture-btn-danger" style={{ width: '120px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }} onClick={handleStop}>
                  <Square size={18} fill="currentColor" /> Stop
                </button>
              </div>
            </motion.div>
          )}

          {status === 'stopped' && (
            <motion.div 
              key="stopped"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-panel" 
              style={{ padding: '3rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--success)' }}>
                <CheckCircle2 size={32} />
                <h2 style={{ fontSize: '2rem', fontWeight: 600, color: 'var(--text-primary)' }}>Lecture captured</h2>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>Your lecture has been safely stored on this device.</p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px' }}>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '4px' }}>Duration</div>
                  <div style={{ fontSize: '1.2rem', fontFamily: 'var(--font-mono)' }}>{formatTime(duration)}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '4px' }}>Visual Events</div>
                  <div style={{ fontSize: '1.2rem', fontFamily: 'var(--font-mono)' }}>{session?.events_count || 0}</div>
                </div>
                <div style={{ gridColumn: '1 / -1', marginTop: '0.5rem' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '4px' }}>Storage Location</div>
                  <div style={{ fontSize: '0.9rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>
                    backend/video_engine/recordings/.../{session?.session_id}.mp4
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button className="capture-btn-primary" onClick={() => setStatus('idle')}>Start New Lecture</button>
              </div>
            </motion.div>
          )}

          {status === 'error' && (
             <div className="glass-panel" style={{ padding: '3rem' }}>
                <AlertCircle size={32} color="var(--danger)" style={{ marginBottom: '1rem' }} />
                <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Recording failed</h2>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>{errorMessage}</p>
                <button className="capture-btn-secondary" onClick={() => setStatus('idle')}>Back to Setup</button>
             </div>
          )}
        </AnimatePresence>
      </div>

      {/* Right Column: Live Processing Pipeline */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        
        {/* Pipeline Visualization */}
        <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1.5rem' }}>
            <Activity size={18} color="var(--accent)" />
            <h3 style={{ fontSize: '0.9rem', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Live Processing Pipeline</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
             {status === 'idle' ? (
                <div style={{ padding: '2rem 0', textAlign: 'center', color: 'var(--text-muted)' }}>
                  Start lecture to initialize engine.
                </div>
             ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <PipelineStage icon="🎤" label="Speech Recognition" state={status === 'recording' ? 'processing' : (status === 'stopped' ? 'completed' : 'pending')} />
                  <PipelineStage icon="👁" label="Visual Perception" state={status === 'recording' ? 'processing' : (status === 'stopped' ? 'completed' : 'pending')} />
                  <PipelineStage icon="🔗" label="Temporal Fusion" state={duration > 5 && status === 'recording' ? 'processing' : (status === 'stopped' ? 'completed' : 'pending')} />
                  <PipelineStage icon="🧠" label="Semantic Understanding" state={duration > 10 && status === 'recording' ? 'processing' : (status === 'stopped' ? 'completed' : 'pending')} />
                  <PipelineStage icon="🛡" label="Evidence Grounding" state={duration > 15 && status === 'recording' ? 'processing' : (status === 'stopped' ? 'completed' : 'pending')} />
                  <PipelineStage icon="📚" label="Lecture Memory" state={duration > 20 && status === 'recording' ? 'processing' : (status === 'stopped' ? 'completed' : 'pending')} />
                </div>
             )}
          </div>
        </div>

        {/* Live Transcript (Demo) */}
        <div className="glass-panel" style={{ flex: 1, padding: '2rem', display: 'flex', flexDirection: 'column', maxHeight: '400px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
            <Mic size={18} color="var(--success)" />
            <h3 style={{ fontSize: '0.9rem', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Live Transcript</h3>
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {status === 'idle' ? (
               <div style={{ margin: 'auto', color: 'var(--text-muted)' }}>Waiting for speech...</div>
            ) : (
               <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                 {duration > 2 && <TranscriptLine time="00:02" text="Alright everyone, let's get started." />}
                 {duration > 15 && <TranscriptLine time="00:15" text="Today we're going to talk about basic electrical engineering." />}
                 {duration > 30 && <TranscriptLine time="00:30" text="First, let's review Ohm's law." />}
                 {duration > 42 && <TranscriptLine time="00:42" text="Current is equal to voltage divided by resistance." />}
                 {status === 'recording' && <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}><span className="status-dot pulse" style={{ background: 'var(--text-muted)', margin: 0 }} /> Listening...</div>}
               </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}

// Helper components for the pipeline
function PipelineStage({ icon, label, state }) {
  const colors = {
    pending: 'var(--text-muted)',
    processing: 'var(--accent)',
    completed: 'var(--success)',
    error: 'var(--danger)'
  };
  const bgs = {
    pending: 'rgba(255,255,255,0.05)',
    processing: 'rgba(94, 106, 210, 0.1)',
    completed: 'rgba(52, 211, 153, 0.1)',
    error: 'rgba(248, 113, 113, 0.1)'
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', background: bgs[state], borderRadius: '8px', border: `1px solid ${state === 'processing' ? 'var(--accent)' : 'transparent'}`, transition: 'all 0.3s' }}>
      <div style={{ fontSize: '1.2rem' }}>{icon}</div>
      <div style={{ flex: 1, fontWeight: 500, color: 'var(--text-primary)' }}>{label}</div>
      <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 600, color: colors[state], display: 'flex', alignItems: 'center', gap: '6px' }}>
        {state === 'processing' && <span className="status-dot pulse" style={{ background: colors[state], margin: 0 }} />}
        {state}
      </div>
    </div>
  );
}

function TranscriptLine({ time, text }) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'flex', gap: '12px' }}>
      <div style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', paddingTop: '2px' }}>{time}</div>
      <div style={{ flex: 1, fontSize: '0.95rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
        <span style={{ color: 'var(--accent)', fontWeight: 500, marginRight: '8px', fontSize: '0.8rem' }}>TEACHER</span>
        {text}
      </div>
    </motion.div>
  );
}

