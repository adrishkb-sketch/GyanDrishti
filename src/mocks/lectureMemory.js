export const mockLectureMemory = {
  session_id: "lecture_20261006_143000",
  title: "Basic Electrical Engineering",
  subject: "EE 101",
  date: "October 6, 2026",
  duration: 3600, // 1h in seconds
  storage_local: true,
  overview: "This lecture introduces the foundational concepts of electrical engineering. We cover Ohm's Law and Kirchhoff's laws, including their practical applications in basic circuit analysis.",
  
  timeline_events: [
    { timestamp: 632, type: "concept", label: "Important concept", details: "Teacher explains Ohm's Law" }, // 10:32
    { timestamp: 641, type: "visual", label: "Visual change", details: "Board shows: I = V/R" }, // 10:41
    { timestamp: 644, type: "multimodal", label: "Multimodal agreement", details: "Speech + visual evidence agree" }, // 10:44
    { timestamp: 680, type: "concept", label: "Important concept", details: "Teacher discusses Kirchhoff's law" }, // 11:20
    { timestamp: 702, type: "multimodal", label: "Conflict detected", details: "Visual evidence conflicts with speech" } // 11:42
  ],

  concepts: [
    {
      id: "c1",
      name: "Ohm's Law",
      explanation: "A fundamental law stating that the current through a conductor between two points is directly proportional to the voltage across the two points. It is typically represented as I = V/R.",
      timestamp: 632,
      evidence: {
        speech: "Current is equal to voltage divided by resistance.",
        visual: "I = V/R",
        status: "MULTIMODAL SUPPORTED"
      }
    },
    {
      id: "c2",
      name: "Kirchhoff's Laws",
      explanation: "Includes Kirchhoff's Current Law (KCL) which states that the total current entering a junction must equal the total current leaving it, and Kirchhoff's Voltage Law (KVL) which states that the sum of all voltages around any closed loop in a circuit must equal zero.",
      timestamp: 680,
      evidence: {
        speech: "The sum of currents entering a node is zero.",
        visual: "Sum(I) = 0",
        status: "MULTIMODAL SUPPORTED"
      }
    }
  ],

  definitions: [
    {
      term: "Current (I)",
      definition: "The rate of flow of electric charge.",
      timestamp: 635
    }
  ],

  equations: [
    {
      name: "Ohm's Law Equation",
      representation: "I = V/R",
      explanation: "Calculates current (I) given voltage (V) and resistance (R).",
      timestamp: 641,
      evidence: {
        speech: "current is equal to voltage divided by resistance",
        visual: "I = V/R",
        status: "MULTIMODAL SUPPORTED",
        temporal_match: "10:44"
      }
    },
    {
      name: "Incorrect Equation Example",
      representation: "I = V × R",
      explanation: "This equation is incorrectly written on the board during a discussion about power.",
      timestamp: 702,
      evidence: {
        speech: "I = V/R",
        visual: "I = V×R",
        status: "CONFLICT",
        temporal_match: "11:42"
      }
    }
  ],

  important_points: [
    { point: "Ohm's Law only applies to ohmic materials where resistance is constant.", timestamp: 650 },
    { point: "Kirchhoff's Current Law is based on the conservation of charge.", timestamp: 690 }
  ],

  visual_references: [
    {
      timestamp: 641,
      source: "Camera",
      event_type: "Board Writing",
      local_frame_reference: "I = V/R on whiteboard",
      description: "Teacher writes Ohm's Law on the board."
    },
    {
      timestamp: 702,
      source: "Camera",
      event_type: "Board Writing",
      local_frame_reference: "Conflicting Equation",
      description: "Teacher accidentally writes I = V×R while saying I = V/R."
    }
  ],

  revision_questions: [
    {
      question: "According to Ohm's Law, what happens to the current if the resistance is doubled while the voltage remains constant?",
      answer: "The current will be halved.",
      timestamp: 645
    },
    {
      question: "What conservation principle is Kirchhoff's Current Law based on?",
      answer: "The conservation of electric charge.",
      timestamp: 695
    }
  ]
};
