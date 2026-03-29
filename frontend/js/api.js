const API = {
  token() {
    return localStorage.getItem("token");
  },

  async request(path, options = {}) {
    const headers = new Headers(options.headers || {});
    if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    if (this.token()) {
      headers.set("Authorization", `Bearer ${this.token()}`);
    }
    const response = await fetch(path, { ...options, headers });
    if (response.status === 401) {
      localStorage.removeItem("token");
      if (!window.location.pathname.endsWith("/")) {
        window.location.href = "/";
      }
    }
    return response;
  },

  async json(path, options = {}) {
    const response = await this.request(path, options);
    if (!response.ok) {
      const payload = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(payload.detail || "Request failed");
    }
    return response.json();
  },
};

