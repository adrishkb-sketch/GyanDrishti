export const mockLectureMemory = {
  session_id: "lecture_20261006_143000",
  title: "Introduction to Quantum Mechanics",
  subject: "Physics 401",
  date: "October 6, 2026",
  duration: 6120, // 1h 42m in seconds
  storage_local: true,
  overview: "This lecture introduces the foundational concepts of quantum mechanics, moving away from classical deterministic physics into probabilistic models. We cover the wave-particle duality, the Schrödinger equation, and the uncertainty principle.",
  
  timeline_events: [
    { timestamp: 120, type: "speech", label: "Speech", details: "Welcome to Physics 401. Today we begin our journey into Quantum Mechanics." },
    { timestamp: 450, type: "concept", label: "Important concept", details: "Wave-Particle Duality introduced." },
    { timestamp: 900, type: "visual", label: "Visual change", details: "Slide changed: Double-Slit Experiment" },
    { timestamp: 1420, type: "equation", label: "Equation", details: "Schrödinger Equation written on board." },
    { timestamp: 2400, type: "multimodal", label: "Multimodal", details: "Professor points to probability distribution graph while explaining Born rule." },
    { timestamp: 3500, type: "concept", label: "Important concept", details: "Heisenberg's Uncertainty Principle." }
  ],

  concepts: [
    {
      id: "c1",
      name: "Wave-Particle Duality",
      explanation: "The concept that every particle or quantum entity may be described as either a particle or a wave. It expresses the inability of the classical concepts 'particle' or 'wave' to fully describe the behavior of quantum-scale objects.",
      timestamp: 450
    },
    {
      id: "c2",
      name: "Heisenberg's Uncertainty Principle",
      explanation: "States that there is a fundamental limit to the precision with which certain pairs of physical properties of a particle, known as complementary variables (like position and momentum), can be known.",
      timestamp: 3500
    }
  ],

  definitions: [
    {
      term: "Wavefunction (Ψ)",
      definition: "A mathematical description of the quantum state of an isolated quantum system. The probability density of finding a particle at a given point is proportional to the square of the magnitude of the wavefunction.",
      timestamp: 1200
    }
  ],

  equations: [
    {
      name: "Time-Dependent Schrödinger Equation",
      representation: "iℏ ∂Ψ/∂t = ĤΨ",
      explanation: "Describes how the quantum state of a physical system changes in time. Ĥ is the Hamiltonian operator, representing the total energy of the system.",
      timestamp: 1420
    }
  ],

  important_points: [
    { point: "Classical physics fails at the atomic scale because it predicts deterministic outcomes.", timestamp: 300 },
    { point: "The act of measurement in quantum mechanics collapses the wavefunction.", timestamp: 4200 },
    { point: "Quantum entanglement implies non-local correlations between particles.", timestamp: 5400 }
  ],

  visual_references: [
    {
      timestamp: 900,
      source: "Screen",
      event_type: "Slide Change",
      local_frame_reference: "Double Slit Experiment Setup", // Using text placeholder instead of actual image paths
      description: "Diagram showing interference pattern from electron beam."
    },
    {
      timestamp: 2400,
      source: "Camera",
      event_type: "Board Writing",
      local_frame_reference: "Probability Density Graph",
      description: "Hand-drawn graph of a Gaussian wave packet."
    }
  ],

  revision_questions: [
    {
      question: "What is the physical significance of the squared magnitude of a wavefunction (|Ψ|²)?",
      answer: "According to the Born rule, |Ψ|² represents the probability density of finding a particle at a specific position and time.",
      timestamp: 2500
    },
    {
      question: "Why can't we know both the exact position and exact momentum of an electron simultaneously?",
      answer: "Due to Heisenberg's Uncertainty Principle, which states that the product of the uncertainties in position and momentum must be greater than or equal to ℏ/2.",
      timestamp: 3600
    }
  ]
};
