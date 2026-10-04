const API_BASE = '/api';

export const api = {
  // Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  // Memories & Ingestion
  async uploadAudio(file) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/memories/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async getMemories(skip = 0, limit = 50, era = null, category = null) {
    let url = `${API_BASE}/memories?skip=${skip}&limit=${limit}`;
    if (era) url += `&era=${encodeURIComponent(era)}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch memories');
    return res.json();
  },

  async getTimeline() {
    const res = await fetch(`${API_BASE}/memories/timeline`);
    if (!res.ok) throw new Error('Failed to fetch timeline metadata');
    return res.json();
  },

  async getAudioRecords(skip = 0, limit = 50) {
    const res = await fetch(`${API_BASE}/memories/audio?skip=${skip}&limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch vaulted audio records');
    return res.json();
  },

  async getMemory(id) {
    const res = await fetch(`${API_BASE}/memories/details/${id}`);
    if (!res.ok) throw new Error('Failed to fetch memory details');
    return res.json();
  },

  getAudioStreamUrl(audioId) {
    return `${API_BASE}/memories/audio/${audioId}/stream`;
  },

  // Semantic Search
  async searchMemories(query, limit = 5) {
    const res = await fetch(`${API_BASE}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit }),
    });
    if (!res.ok) throw new Error('Search failed');
    return res.json();
  },

  // Grounded RAG QA
  async askGrandfather(question) {
    const res = await fetch(`${API_BASE}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) throw new Error('Failed to consult grandfather memory');
    return res.json();
  },

  // Then vs Now (Signature Feature)
  async compareMemories(params = {}) {
    const res = await fetch(`${API_BASE}/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error('Failed to generate Then vs Now comparison');
    return res.json();
  },

  async getOrGenerateComparison(memoryId) {
    if (typeof memoryId === 'object') {
      return this.compareMemories(memoryId);
    }
    const res = await fetch(`${API_BASE}/compare/${memoryId}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to generate Then vs Now comparison');
    return res.json();
  },

  async listComparisons() {
    const res = await fetch(`${API_BASE}/compare`);
    if (!res.ok) throw new Error('Failed to fetch comparisons');
    return res.json();
  }
};
