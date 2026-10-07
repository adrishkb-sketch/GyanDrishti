export const API_URL = 'http://localhost:8000/api/video';

export async function fetchDevices() {
  const res = await fetch(`${API_URL}/devices`);
  if (!res.ok) throw new Error('Failed to fetch devices');
  return res.json();
}

export async function startSession(cameraId, screenId) {
  const res = await fetch(`${API_URL}/session/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ camera_id: cameraId, screen_id: screenId })
  });
  if (!res.ok) throw new Error('Failed to start session');
  return res.json();
}

export async function pauseSession() {
  const res = await fetch(`${API_URL}/session/pause`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to pause session');
  return res.json();
}

export async function resumeSession() {
  const res = await fetch(`${API_URL}/session/resume`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to resume session');
  return res.json();
}

export async function stopSession() {
  const res = await fetch(`${API_URL}/session/stop`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to stop session');
  return res.json();
}

export async function getSessionStatus() {
  const res = await fetch(`${API_URL}/session/status`);
  if (!res.ok) throw new Error('Failed to fetch session status');
  return res.json();
}

export async function saveLectureMemory(data) {
  const res = await fetch('http://localhost:8000/api/lectures', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to save lecture memory');
  return res.json();
}
