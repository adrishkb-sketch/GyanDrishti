// Frontend-facing API types for Lecture Memory

export interface TimelineEvent {
  timestamp: number;
  type: 'speech' | 'visual' | 'keyframe' | 'equation' | 'concept' | 'multimodal';
  label: string;
  details?: string;
}

export interface Concept {
  id: string;
  name: string;
  explanation: string;
  timestamp: number;
}

export interface Definition {
  term: string;
  definition: string;
  timestamp: number;
}

export interface Equation {
  name: string;
  representation: string; // Text or LaTeX representation
  explanation: string;
  timestamp: number;
}

export interface ImportantPoint {
  point: string;
  timestamp: number;
}

export interface VisualReference {
  timestamp: number;
  source: string;
  event_type: string;
  local_frame_reference: string;
  description?: string;
}

export interface QuestionCandidate {
  question: string;
  answer: string;
  timestamp: number;
}

export interface LectureMemory {
  session_id: string;
  title: string;
  subject: string;
  date: string;
  duration: number; // in seconds
  storage_local: boolean;
  overview: string;
  timeline_events: TimelineEvent[];
  concepts: Concept[];
  definitions: Definition[];
  equations: Equation[];
  important_points: ImportantPoint[];
  visual_references: VisualReference[];
  revision_questions: QuestionCandidate[];
}
