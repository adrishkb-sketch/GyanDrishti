import React, { useRef } from 'react';
import { Link } from 'react-router-dom';
import { BrainCircuit, Play, Sparkles, BookOpen, GraduationCap, Video, Users, MessageSquare, Zap, BarChart, ChevronRight, CheckSquare } from 'lucide-react';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';

const Landing = () => {
  const { scrollYProgress } = useScroll();
  
  // Parallax effects
  const heroY = useTransform(scrollYProgress, [0, 1], ['0%', '50%']);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);
  
  const staggerContainer = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.2 }
    }
  };

  const fadeInUp = {
    hidden: { opacity: 0, y: 40 },
    show: { opacity: 1, y: 0, transition: { duration: 0.8, ease: "easeOut" } }
  };

  const textReveal = {
    hidden: { opacity: 0, y: 20, rotateX: 90 },
    show: { opacity: 1, y: 0, rotateX: 0, transition: { duration: 1, ease: "easeOut" } }
  };

  return (
    <div style={{ padding: '0', margin: 0, overflowX: 'hidden', background: 'var(--bg-darker)' }}>
      
      {/* Navigation */}
      <motion.nav 
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        style={{ padding: '24px 48px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'fixed', width: '100%', top: 0, zIndex: 100, background: 'rgba(2, 6, 23, 0.6)', backdropFilter: 'blur(20px)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <motion.div whileHover={{ rotate: 180 }} transition={{ duration: 0.5 }}>
            <BrainCircuit color="var(--primary-color)" size={32} />
          </motion.div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, letterSpacing: '-0.5px', color: 'white' }}>
            Lecture<span className="gradient-text">AI</span>
          </h1>
        </div>
        <div style={{ display: 'flex', gap: '32px', alignItems: 'center' }}>
          <a href="#features" className="hover-underline" style={{ color: 'var(--text-light)', textDecoration: 'none', fontSize: '15px' }}>Features</a>
          <a href="#how-it-works" className="hover-underline" style={{ color: 'var(--text-light)', textDecoration: 'none', fontSize: '15px' }}>How it Works</a>
          <div style={{ display: 'flex', gap: '16px' }}>
            <Link to="/login" className="btn-secondary" style={{ padding: '10px 20px' }}>Sign In</Link>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link to="/dashboard/teacher" className="btn-primary" style={{ padding: '10px 20px', display: 'flex', alignItems: 'center', gap: '6px' }}><Video size={16} /> Record Lecture</Link>
            </motion.div>
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <motion.main 
        style={{ 
          minHeight: '100vh', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          padding: '120px 5% 0 10%',
          position: 'relative',
          y: heroY,
          opacity: heroOpacity,
          backgroundImage: 'linear-gradient(to right, rgba(2,6,23,0.9) 0%, rgba(2,6,23,0.7) 50%, rgba(2,6,23,0.4) 100%), url("/hero_bg.jpg")',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed'
        }}
      >
        
        {/* Decorative elements */}
        <motion.div 
          animate={{ scale: [1, 1.2, 1], opacity: [0.2, 0.4, 0.2] }} 
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          style={{
            position: 'absolute',
            top: '20%', left: '5%',
            width: '300px', height: '300px',
            background: 'var(--primary-color)',
            filter: 'blur(150px)', zIndex: 0
          }} 
        />

        <motion.div 
          animate={{ scale: [1, 1.3, 1], opacity: [0.1, 0.3, 0.1] }} 
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          style={{
            position: 'absolute',
            bottom: '10%', right: '10%',
            width: '400px', height: '400px',
            background: 'var(--secondary-color)',
            filter: 'blur(180px)', zIndex: 0
          }} 
        />

        {/* Content */}
        <motion.div 
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          style={{ maxWidth: '600px', zIndex: 1, perspective: '1000px' }}
        >
          <motion.div variants={fadeInUp} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px' }}>
            <span style={{ background: 'rgba(99,102,241,0.2)', padding: '6px 16px', borderRadius: '20px', color: 'var(--primary-color)', fontSize: '14px', fontWeight: 600, border: '1px solid rgba(99,102,241,0.3)', display: 'flex', alignItems: 'center' }}>
              <motion.div animate={{ rotate: [0, 15, -15, 0] }} transition={{ repeat: Infinity, duration: 2 }}>
                <Sparkles size={14} style={{ marginRight: '6px' }}/>
              </motion.div>
              Revolutionizing Higher Education
            </span>
          </motion.div>
          
          <motion.h1 variants={textReveal} style={{ fontSize: '72px', fontWeight: 800, lineHeight: 1.1, marginBottom: '24px', transformStyle: 'preserve-3d' }}>
            Transform Lectures into <br />
            <motion.span 
              className="gradient-text"
              initial={{ backgroundPosition: '0% 50%' }}
              animate={{ backgroundPosition: '100% 50%' }}
              transition={{ duration: 5, repeat: Infinity, repeatType: 'reverse' }}
              style={{ backgroundSize: '200% 200%' }}
            >Interactive Intelligence</motion.span>
          </motion.h1>
          
          <motion.p variants={fadeInUp} style={{ fontSize: '20px', color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: '40px' }}>
            Seamlessly record classes, instantly generate AI study notes, and let students interact with the material. Drive engagement with smart analytics and automated polls.
          </motion.p>
          
          <motion.div variants={fadeInUp} style={{ display: 'flex', gap: '16px' }}>
            <motion.div whileHover={{ scale: 1.05, boxShadow: "0 0 30px rgba(99,102,241,0.6)" }} whileTap={{ scale: 0.95 }}>
              <Link to="/dashboard/teacher" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '18px', padding: '16px 32px' }}>
                Record Lecture <Video size={20} />
              </Link>
            </motion.div>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <a href="#features" className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '18px', padding: '16px 32px', background: 'rgba(255,255,255,0.05)' }}>
                Explore Features
              </a>
            </motion.div>
          </motion.div>
          
          <motion.div variants={fadeInUp} style={{ display: 'flex', alignItems: 'center', gap: '24px', marginTop: '64px', color: 'var(--text-muted)' }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5, duration: 2 }} style={{ fontSize: '32px', fontWeight: 800, color: 'var(--text-light)' }}>500+</motion.span>
              <span style={{ fontSize: '14px' }}>Universities</span>
            </div>
            <div style={{ width: '1px', height: '40px', background: 'rgba(255,255,255,0.1)' }}></div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.7, duration: 2 }} style={{ fontSize: '32px', fontWeight: 800, color: 'var(--text-light)' }}>1M+</motion.span>
              <span style={{ fontSize: '14px' }}>Lectures Processed</span>
            </div>
          </motion.div>
        </motion.div>

        {/* 3D-like Visual Element */}
        <motion.div 
          initial={{ opacity: 0, x: 100, rotateY: 30 }}
          animate={{ opacity: 1, x: 0, rotateY: -15, rotateX: 5 }}
          transition={{ duration: 1.2, ease: "easeOut", delay: 0.5 }}
          whileHover={{ rotateY: 0, rotateX: 0, scale: 1.05 }}
          style={{ zIndex: 1, position: 'relative', marginTop: '-50px', perspective: '1000px' }}
        >
          <div className="glass-panel" style={{ 
            width: '450px', 
            height: '550px', 
            padding: '24px', 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '16px',
            boxShadow: '-20px 20px 40px rgba(0,0,0,0.5), 0 0 40px rgba(99,102,241,0.2)',
            border: '1px solid rgba(255,255,255,0.2)',
            transformStyle: 'preserve-3d'
          }}>
            {/* Mock UI in Glass Panel */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '16px', transform: 'translateZ(20px)' }}>
               <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 8, repeat: Infinity, ease: 'linear' }} style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(45deg, #6366f1, #ec4899)' }}></motion.div>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '16px', color: 'white' }}>Dr. Smith's AI Class</h4>
                    <motion.span animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 2, repeat: Infinity }} style={{ fontSize: '12px', color: 'var(--primary-color)' }}>Generating AI notes...</motion.span>
                  </div>
               </div>
            </div>
            
            <div style={{ flex: 1, background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'hidden', transform: 'translateZ(40px)' }}>
                <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 1 }} style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px', width: '85%' }}>
                  <p style={{ margin: 0, fontSize: '14px', color: 'var(--text-muted)' }}>AI Summary:</p>
                  <p style={{ margin: '4px 0 0', fontSize: '14px', color: 'white' }}>Machine learning models require robust datasets for training.</p>
                </motion.div>
                <motion.div initial={{ x: 20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 2 }} style={{ background: 'rgba(99,102,241,0.2)', padding: '12px', borderRadius: '8px', width: '75%', alignSelf: 'flex-end', borderBottomRightRadius: '0', border: '1px solid rgba(99,102,241,0.3)' }}>
                  <p style={{ margin: 0, fontSize: '14px', color: 'white' }}>What is an example of a robust dataset?</p>
                </motion.div>
                <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 3 }} style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px', width: '85%', borderBottomLeftRadius: '0' }}>
                  <p style={{ margin: 0, fontSize: '14px', color: 'white' }}>ImageNet is a classic example of a robust dataset used in computer vision...</p>
                </motion.div>
            </div>
            
            <div style={{ display: 'flex', gap: '12px', marginTop: 'auto', transform: 'translateZ(60px)' }}>
              <div style={{ flex: 1, height: '40px', background: 'rgba(255,255,255,0.05)', borderRadius: '20px', display: 'flex', alignItems: 'center', padding: '0 16px', border: '1px solid rgba(255,255,255,0.1)' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Ask a question...</span>
              </div>
              <motion.div whileHover={{ scale: 1.1, rotate: 180 }} style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--primary-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 0 15px var(--primary-color)' }}>
                <Sparkles size={20} color="white" />
              </motion.div>
            </div>
          </div>
        </motion.div>
      </motion.main>

      {/* Features Section */}
      <section id="features" style={{ padding: '120px 10%', background: 'rgba(255,255,255,0.02)', position: 'relative' }}>
        <motion.div 
          initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.3 }} variants={staggerContainer}
          style={{ textAlign: 'center', marginBottom: '80px' }}
        >
          <motion.h2 variants={fadeInUp} style={{ fontSize: '48px', fontWeight: 800, marginBottom: '24px', color: 'white' }}>Empowering both <span className="gradient-text">Students</span> and <span className="gradient-text">Teachers</span></motion.h2>
          <motion.p variants={fadeInUp} style={{ fontSize: '20px', color: 'var(--text-muted)', maxWidth: '800px', margin: '0 auto' }}>A unified platform that bridges the gap between teaching and learning through the power of Artificial Intelligence.</motion.p>
        </motion.div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px', perspective: '1000px' }}>
          
          {/* For Students */}
          <motion.div 
            initial={{ opacity: 0, rotateY: -30, x: -50 }}
            whileInView={{ opacity: 1, rotateY: 0, x: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.8 }}
            whileHover={{ y: -10, boxShadow: '0 20px 40px rgba(99,102,241,0.2)' }}
            className="glass-panel" style={{ padding: 0, borderTop: '4px solid var(--primary-color)', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
          >
            <div style={{ height: '250px', width: '100%', position: 'relative', overflow: 'hidden' }}>
              <img src="/student_hero.jpg" alt="Student AI Interface" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: '100%', background: 'linear-gradient(to top, rgba(15,23,42,1), rgba(15,23,42,0))' }}></div>
            </div>
            
            <div style={{ padding: '32px' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '16px', background: 'rgba(99,102,241,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '24px', border: '1px solid rgba(99,102,241,0.3)', marginTop: '-64px', position: 'relative', zIndex: 2, backdropFilter: 'blur(10px)' }}>
                <GraduationCap size={32} color="var(--primary-color)" />
              </div>
              <h3 style={{ fontSize: '32px', marginBottom: '16px', color: 'white' }}>For Students</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '16px', marginBottom: '32px', lineHeight: 1.6 }}>Never miss a beat in class. Interact directly with the lecture material to clarify your doubts instantly.</p>
              
              <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {[
                  { icon: <BookOpen color="var(--primary-color)" />, text: "On-Demand Lecture Notes" },
                  { icon: <MessageSquare color="var(--primary-color)" />, text: "Ask AI Any Question" },
                  { icon: <Zap color="var(--primary-color)" />, text: "Automated Flashcards" }
                ].map((item, i) => (
                  <motion.li key={i} whileHover={{ x: 10 }} style={{ display: 'flex', gap: '16px', alignItems: 'center', color: 'var(--text-light)' }}>
                    <div style={{ background: 'rgba(99,102,241,0.1)', padding: '8px', borderRadius: '8px' }}>{item.icon}</div>
                    <span style={{ fontSize: '18px', fontWeight: 500 }}>{item.text}</span>
                  </motion.li>
                ))}
              </ul>
            </div>
          </motion.div>

          {/* For Teachers */}
          <motion.div 
            initial={{ opacity: 0, rotateY: 30, x: 50 }}
            whileInView={{ opacity: 1, rotateY: 0, x: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.8 }}
            whileHover={{ y: -10, boxShadow: '0 20px 40px rgba(236,72,153,0.2)' }}
            className="glass-panel" style={{ padding: 0, borderTop: '4px solid var(--secondary-color)', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
          >
            <div style={{ height: '250px', width: '100%', position: 'relative', overflow: 'hidden' }}>
              <img src="/teacher_hero.jpg" alt="Teacher Analytics Dashboard" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: '100%', background: 'linear-gradient(to top, rgba(15,23,42,1), rgba(15,23,42,0))' }}></div>
            </div>
            
            <div style={{ padding: '32px' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '16px', background: 'rgba(236,72,153,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '24px', border: '1px solid rgba(236,72,153,0.3)', marginTop: '-64px', position: 'relative', zIndex: 2, backdropFilter: 'blur(10px)' }}>
                <Users size={32} color="var(--secondary-color)" />
              </div>
              <h3 style={{ fontSize: '32px', marginBottom: '16px', color: 'white' }}>For Teachers</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '16px', marginBottom: '32px', lineHeight: 1.6 }}>Focus on teaching, let AI handle the admin work. Gain unprecedented insights into your students' understanding.</p>
              
              <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {[
                  { icon: <BarChart color="var(--secondary-color)" />, text: "Automated Analytics" },
                  { icon: <CheckSquare color="var(--secondary-color)" />, text: "Instant Poll Generation" },
                  { icon: <Video color="var(--secondary-color)" />, text: "One-Click Lecture Recording" }
                ].map((item, i) => (
                  <motion.li key={i} whileHover={{ x: 10 }} style={{ display: 'flex', gap: '16px', alignItems: 'center', color: 'var(--text-light)' }}>
                    <div style={{ background: 'rgba(236,72,153,0.1)', padding: '8px', borderRadius: '8px' }}>{item.icon}</div>
                    <span style={{ fontSize: '18px', fontWeight: 500 }}>{item.text}</span>
                  </motion.li>
                ))}
              </ul>
            </div>
          </motion.div>

        </div>
      </section>

      {/* How it Works */}
      <section id="how-it-works" style={{ padding: '120px 10%', position: 'relative' }}>
        <motion.div 
          initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6 }}
          style={{ textAlign: 'center', marginBottom: '80px' }}
        >
          <h2 style={{ fontSize: '48px', fontWeight: 800, marginBottom: '24px', color: 'white' }}>How It Works</h2>
        </motion.div>

        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '24px', alignItems: 'flex-start', position: 'relative' }}>
          
          {/* Connecting line */}
          <div style={{ position: 'absolute', top: '40px', left: '15%', right: '15%', height: '2px', background: 'linear-gradient(90deg, var(--primary-color), var(--secondary-color))', zIndex: 0, opacity: 0.3 }}></div>

          {[
            { num: 1, title: 'Record Lecture', desc: 'The professor simply clicks record. Our system captures audio, video, and screen sharing.' },
            { num: 2, title: 'AI Processing', desc: 'Our advanced AI transcribes the lecture, extracts key concepts, and creates summary notes instantly.' },
            { num: 3, title: 'Interactive Learning', desc: 'Students interact with the AI to ask questions, while teachers view analytics on what students find confusing.' }
          ].map((step, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6, delay: i * 0.2 }}
              style={{ flex: 1, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 1 }}
            >
              <motion.div 
                whileHover={{ scale: 1.1, rotate: 10 }}
                style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--primary-color), var(--secondary-color))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '32px', fontWeight: 800, marginBottom: '32px', boxShadow: '0 10px 30px rgba(99,102,241,0.5)', color: 'white', border: '4px solid var(--bg-darker)' }}
              >
                {step.num}
              </motion.div>
              <h3 style={{ fontSize: '24px', marginBottom: '16px', color: 'white' }}>{step.title}</h3>
              <p style={{ color: 'var(--text-muted)', lineHeight: 1.6, padding: '0 20px' }}>{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer style={{ padding: '64px 10%', background: 'rgba(0,0,0,0.8)', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <BrainCircuit color="var(--primary-color)" size={24} />
          <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'white' }}>Lecture<span className="gradient-text">AI</span></h2>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
          © 2026 LectureAI Inc. All rights reserved.
        </div>
        <div style={{ display: 'flex', gap: '24px' }}>
          <motion.a whileHover={{ color: 'var(--primary-color)' }} href="#" style={{ color: 'var(--text-muted)', textDecoration: 'none', transition: 'color 0.2s' }}>Privacy Policy</motion.a>
          <motion.a whileHover={{ color: 'var(--primary-color)' }} href="#" style={{ color: 'var(--text-muted)', textDecoration: 'none', transition: 'color 0.2s' }}>Terms of Service</motion.a>
          <motion.a whileHover={{ color: 'var(--primary-color)' }} href="#" style={{ color: 'var(--text-muted)', textDecoration: 'none', transition: 'color 0.2s' }}>Contact</motion.a>
        </div>
      </footer>

    </div>
  );
};

export default Landing;
