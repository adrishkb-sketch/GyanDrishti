import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import StudentDashboard from './pages/StudentDashboard';
import TeacherDashboard from './pages/TeacherDashboard';

import LectureViewer from './pages/LectureViewer';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard/student" element={<StudentDashboard />} />
        <Route path="/dashboard/teacher" element={<TeacherDashboard />} />
        <Route path="/record" element={<TeacherDashboard />} />
        <Route path="/studio" element={<TeacherDashboard />} />
        <Route path="/lectures/:lectureId" element={<LectureViewer />} />
      </Routes>
    </Router>
  );
}

export default App;
