// ─── Shared API config — single source of truth ──────────────────────────────
const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
export const API_V1 = `${API_BASE}/api/v1`;

// ─── Internal fetch wrapper ───────────────────────────────────────────────────
async function request(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const e = new Error(err.detail || `HTTP ${res.status}`);
      e.status = res.status;
      throw e;
    }
    // 204 No Content
    if (res.status === 204) return null;
    return await res.json();
  } catch (err) {
    if (err.name === 'TypeError' && err.message.toLowerCase().includes('fetch')) {
      throw new Error('Backend is not reachable. Make sure it is running on localhost:8000.');
    }
    throw err;
  }
}

// ─── Health ───────────────────────────────────────────────────────────────────
export const checkHealth = () => request(`${API_BASE}/health`);

// ─── Incidents (trailing slash on collection) ─────────────────────────────────
export const listIncidents = (params = {}) => {
  const q = new URLSearchParams();
  if (params.skip  != null) q.set('skip',       params.skip);
  if (params.limit != null) q.set('limit',      params.limit);
  if (params.status)        q.set('status',     params.status);
  if (params.source_cam)    q.set('source_cam', params.source_cam);
  if (params.hours  != null) q.set('hours',     params.hours);
  return request(`${API_V1}/incidents/?${q}`);
};

export const getIncident = (id) => request(`${API_V1}/incidents/${id}`);

export const updateIncident = (id, data) =>
  request(`${API_V1}/incidents/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

export const getIncidentSnapshots = (id) =>
  request(`${API_V1}/incidents/${id}/snapshots`);

// ─── Border pipeline ──────────────────────────────────────────────────────────
/**
 * @param {{
 *   source: string,
 *   source_type: 'file'|'rtsp',
 *   camera_id: string,
 *   confidence_threshold: number,
 *   sample_every_n_frames: number,
 *   fence_y_ratio: number
 * }} payload
 */
export const processBorderSource = (payload) =>
  request(`${API_V1}/border/process`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// ─── Models (trailing slash on collection) ────────────────────────────────────
export const listModels = (status) => {
  const q = status ? `?status=${status}` : '';
  return request(`${API_V1}/models/${q}`);
};

/** Callers must catch 404 and treat it as "no production model yet" */
export const getProductionModel = () => request(`${API_V1}/models/production`);

export const deployModel = (modelId) =>
  request(`${API_V1}/models/deploy`, {
    method: 'POST',
    body: JSON.stringify({ model_id: modelId }),
  });

// ─── Training jobs (trailing slash on collection) ─────────────────────────────
export const listTrainJobs = (params = {}) => {
  const q = new URLSearchParams();
  if (params.skip  != null) q.set('skip',   params.skip);
  if (params.limit != null) q.set('limit',  params.limit);
  if (params.status)        q.set('status', params.status);
  return request(`${API_V1}/models/train/?${q}`);
};

export const getTrainJob  = (id) => request(`${API_V1}/models/train/${id}`);
export const getTrainLogs = (id) => request(`${API_V1}/models/train/${id}/logs`);

export const triggerTraining = (config) =>
  request(`${API_V1}/models/train/`, {
    method: 'POST',
    body: JSON.stringify(config),
  });

// ─── Auto-Train ───────────────────────────────────────────────────────────────
export const startAutoTrain = (data) =>
  request(`${API_V1}/models/auto-train`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getAutoTrainStatus = (jobId) =>
  request(`${API_V1}/models/auto-train/status/${jobId}`);

export const downloadAutoTrainResults = (jobId) =>
  request(`${API_V1}/models/auto-train/download/${jobId}`);
