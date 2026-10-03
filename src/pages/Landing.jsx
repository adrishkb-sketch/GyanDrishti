import React from 'react';
import { Link } from 'react-router-dom';
import { BrainCircuit, Play, Sparkles, BookOpen, GraduationCap } from 'lucide-react';

const Landing = () => {
  return (
    <div style={{ padding: '0', margin: 0, position: 'relative' }}>
      
      {/* Navigation */}
      <nav style={{ padding: '24px 48px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative', zIndex: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <BrainCircuit color="var(--primary-color)" size={32} />
          <h1 style={{ fontSize: '24px', fontWeight: 800, letterSpacing: '-0.5px' }}>
            Lecture<span className="gradient-text">AI</span>
          </h1>
        </div>
        <div>
          <Link to="/login" className="btn-secondary" style={{ marginRight: '16px' }}>Sign In</Link>
          <Link to="/login" className="btn-primary">Get Started</Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main style={{ 
        minHeight: '85vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        padding: '0 5% 0 10%',
        position: 'relative'
      }}>
        
        {/* Decorative elements */}
        <div style={{
          position: 'absolute',
          top: '20%', left: '5%',
          width: '300px', height: '300px',
          background: 'var(--primary-color)',
          filter: 'blur(150px)', opacity: 0.3, zIndex: 0
        }} />

        <div style={{
          position: 'absolute',
          bottom: '10%', right: '10%',
          width: '400px', height: '400px',
          background: 'var(--secondary-color)',
          filter: 'blur(180px)', opacity: 0.2, zIndex: 0
        }} />

        {/* Content */}
        <div style={{ maxWidth: '600px', zIndex: 1 }} className="fade-in">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
            <span style={{ background: 'rgba(99,102,241,0.2)', padding: '6px 12px', borderRadius: '20px', color: 'var(--primary-color)', fontSize: '14px', fontWeight: 600 }}>
              <Sparkles size={14} style={{ display: 'inline', marginRight: '6px' }}/>
              The Future of Learning
            </span>
          </div>
          
          <h1 style={{ fontSize: '64px', fontWeight: 800, lineHeight: 1.1, marginBottom: '24px' }}>
            Transform Lectures into <br />
            <span className="gradient-text">Intelligent Knowledge</span>
          </h1>
          
          <p style={{ fontSize: '20px', color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: '40px' }}>
            Record, convert, and interact. Our AI turns classroom lectures into interactive study materials. Ask questions, track attendance, and gauge understanding instantly.
          </p>
          
          <div style={{ display: 'flex', gap: '16px' }}>
            <Link to="/login" className="btn-primary animate-pulse-glow" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '18px', padding: '16px 32px' }}>
              Start for Free <Play size={20} />
            </Link>
            <a href="#features" className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '18px', padding: '16px 32px' }}>
              Explore Features
            </a>
          </div>
        </div>

        {/* 3D-like Visual Element */}
        <div className="animate-float" style={{ zIndex: 1, position: 'relative' }}>
          <div className="glass-panel" style={{ 
            width: '450px', 
            height: '550px', 
            padding: '24px', 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '16px',
            transform: 'perspective(1000px) rotateY(-15deg) rotateX(5deg)',
            boxShadow: '-20px 20px 40px rgba(0,0,0,0.4)',
            border: '1px solid rgba(255,255,255,0.15)'
          }}>
            {/* Mock UI in Glass Panel */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '16px' }}>
               <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(45deg, #6366f1, #ec4899)' }}></div>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '16px' }}>Dr. Smith's AI Class</h4>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Generating AI notes...</span>
                  </div>
               </div>
            </div>
            
            <div style={{ flex: 1, background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px', width: '80%' }}>
                  <p style={{ margin: 0, fontSize: '14px', color: 'var(--text-muted)' }}>AI Summary:</p>
                  <p style={{ margin: '4px 0 0', fontSize: '14px' }}>Machine learning models require robust datasets for training.</p>
                </div>
                <div style={{ background: 'rgba(99,102,241,0.2)', padding: '12px', borderRadius: '8px', width: '70%', alignSelf: 'flex-end', borderBottomRightRadius: '0' }}>
                  <p style={{ margin: 0, fontSize: '14px' }}>What is an example of a robust dataset?</p>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px', width: '80%', borderBottomLeftRadius: '0' }}>
                  <p style={{ margin: 0, fontSize: '14px' }}>ImageNet is a classic example of a robust dataset used in computer vision...</p>
                </div>
            </div>
            
            <div style={{ display: 'flex', gap: '12px', marginTop: 'auto' }}>
              <div style={{ flex: 1, height: '40px', background: 'rgba(255,255,255,0.05)', borderRadius: '20px', display: 'flex', alignItems: 'center', padding: '0 16px' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Ask a question...</span>
              </div>
              <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--primary-color)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Sparkles size={20} color="white" />
              </div>
            </div>
          </div>
        </div>

      </main>

    </div>
  );
};

export default Landing;
