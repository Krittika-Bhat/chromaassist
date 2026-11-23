const API_BASE_URL = 'http://localhost:8000';

/**
 * Handle API responses and extract meaningful error messages
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'An unexpected error occurred.';
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        if (typeof errorJson.detail === 'string') {
          errorDetail = errorJson.detail;
        } else if (errorJson.detail.message) {
          errorDetail = errorJson.detail.message;
        } else if (Array.isArray(errorJson.detail)) {
          errorDetail = errorJson.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
        } else {
          errorDetail = JSON.stringify(errorJson.detail);
        }
      }
    } catch {
      errorDetail = `${response.status}: ${response.statusText}`;
    }
    const err = new Error(errorDetail);
    err.status = response.status;
    throw err;
  }
  return response.json();
}

/**
 * Health check
 */
export async function checkHealth() {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  return handleResponse(res);
}

/**
 * Process single image
 * Returns { processed_image_b64, metrics }
 */
export async function processImage({
  file,
  mode,
  deficiency = 'deuteranopia',
  severity = 1.0,
  method = 'global',
  colormap = 'viridis',
}) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mode', mode);
  formData.append('deficiency', deficiency);
  formData.append('severity', severity.toString());
  formData.append('method', method);
  formData.append('colormap', colormap);

  const res = await fetch(`${API_BASE_URL}/api/process`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(res);
}

/**
 * Compare all (4-way)
 * Returns { original_b64, simulated_b64, corrected_b64, corrected_simulated_b64, metrics }
 */
export async function compareImages({
  file,
  deficiency = 'deuteranopia',
  severity = 1.0,
  method = 'global',
}) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('deficiency', deficiency);
  formData.append('severity', severity.toString());
  formData.append('method', method);

  const res = await fetch(`${API_BASE_URL}/api/compare`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(res);
}
