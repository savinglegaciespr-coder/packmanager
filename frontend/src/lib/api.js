import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_URL = `${BACKEND_URL}/api`;

const client = axios.create({
  baseURL: API_URL,
  timeout: 15000,
});

const cache = new Map();
const withCache = async (key, ttlMs, fetcher) => {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.ts < ttlMs) return cached.data;
  const data = await fetcher();
  cache.set(key, { data, ts: Date.now() });
  return data;
};
export const invalidateCache = (key) => cache.delete(key);

const adminCache = new Map();
const ADMIN_TTL = 30_000;

const withAdminCache = async (key, fetcher) => {
  const cached = adminCache.get(key);
  if (cached && Date.now() - cached.ts < ADMIN_TTL) return cached.data;
  const data = await fetcher();
  adminCache.set(key, { data, ts: Date.now() });
  return data;
};

export const clearAdminCache = () => adminCache.clear();

const bustAdminPrefix = (prefix) => {
  for (const key of adminCache.keys()) {
    if (key.startsWith(prefix)) adminCache.delete(key);
  }
};

const authConfig = (token) => ({
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

const normalizeError = (error) => {
  throw new Error(error?.response?.data?.detail || error.message || "Unexpected error");
};

export const publicApi = {
  async getConfig() {
    return withCache("public:config", 60_000, async () => {
      try {
        const response = await client.get("/public/config");
        return response.data;
      } catch (error) {
        return normalizeError(error);
      }
    });
  },
  async getPrograms() {
    return withCache("public:programs", 60_000, async () => {
      try {
        const response = await client.get("/public/programs");
        return response.data;
      } catch (error) {
        return normalizeError(error);
      }
    });
  },
  async getWeeks(programId) {
    try {
      const response = await client.get("/public/weeks", { params: { program_id: programId } });
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getBookingByPaymentToken(token) {
    try {
      const response = await client.get(`/public/booking-payment/${token}`);
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getBookingByDepositToken(token) {
    try {
      const response = await client.get(`/public/booking-deposit/${token}`);
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async createStripeDepositSession(token) {
    try {
      const response = await client.post(`/public/booking-deposit/${token}/create-stripe-session`);
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async uploadFinalPaymentByToken(token, file) {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await client.post(`/public/booking-payment/${token}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async createStripeFinalSession(token) {
    try {
      const response = await client.post(`/public/booking-payment/${token}/create-stripe-final-session`);
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async submitBooking(formData) {
    try {
      const response = await client.post("/public/bookings", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async createStripeSession(bookingId) {
    try {
      const response = await client.post(`/public/bookings/${bookingId}/create-stripe-session`);
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
};

export const adminApi = {
  async login(payload) {
    try {
      const response = await client.post("/auth/login", payload);
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async me(token) {
    try {
      const response = await client.get("/auth/me", authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getDashboard(token) {
    return withAdminCache("admin:dashboard", async () => {
      try {
        const response = await client.get("/admin/dashboard", authConfig(token));
        return response.data;
      } catch (error) {
        return normalizeError(error);
      }
    });
  },
  async getBookings(token, params = {}) {
    const page = params.page || 1;
    return withAdminCache(`admin:bookings:p${page}`, async () => {
      try {
        const response = await client.get("/admin/bookings", { ...authConfig(token), params });
        return response.data;
      } catch (error) {
        return normalizeError(error);
      }
    });
  },
  async updateBooking(token, bookingId, payload) {
    try {
      const response = await client.patch(`/admin/bookings/${bookingId}`, payload, authConfig(token));
      bustAdminPrefix("admin:bookings:");
      adminCache.delete("admin:dashboard");
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async createManualBooking(token, payload) {
    try {
      const response = await client.post("/admin/bookings/manual", payload, authConfig(token));
      bustAdminPrefix("admin:bookings:");
      adminCache.delete("admin:dashboard");
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getPrograms(token) {
    return withAdminCache("admin:programs", async () => {
      try {
        const response = await client.get("/admin/programs", authConfig(token));
        return response.data;
      } catch (error) {
        return normalizeError(error);
      }
    });
  },
  async createProgram(token, payload) {
    try {
      const response = await client.post("/admin/programs", payload, authConfig(token));
      invalidateCache("public:programs");
      adminCache.delete("admin:programs");
      adminCache.delete("admin:dashboard");
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async updateProgram(token, programId, payload) {
    try {
      const response = await client.put(`/admin/programs/${programId}`, payload, authConfig(token));
      invalidateCache("public:programs");
      adminCache.delete("admin:programs");
      adminCache.delete("admin:dashboard");
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getCapacity(token) {
    return withAdminCache("admin:capacity", async () => {
      try {
        const response = await client.get("/admin/capacity", authConfig(token));
        return response.data;
      } catch (error) {
        return normalizeError(error);
      }
    });
  },
  async updateCapacity(token, weekStart, capacity) {
    try {
      const response = await client.put(`/admin/capacity/${weekStart}`, { capacity }, authConfig(token));
      adminCache.delete("admin:capacity");
      adminCache.delete("admin:dashboard");
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getSettings(token) {
    return withAdminCache("admin:settings", async () => {
      try {
        const response = await client.get("/admin/settings", authConfig(token));
        return response.data;
      } catch (error) {
        return normalizeError(error);
      }
    });
  },
  async updateSettings(token, payload) {
    try {
      const response = await client.put("/admin/settings", payload, authConfig(token));
      invalidateCache("public:config");
      adminCache.delete("admin:settings");
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async uploadLogo(token, file) {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await client.post("/admin/settings/logo", formData, {
        ...authConfig(token),
        headers: {
          ...authConfig(token).headers,
          "Content-Type": "multipart/form-data",
        },
      });
      adminCache.delete("admin:settings");
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async uploadLandingHeroImage(token, file) {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await client.post("/admin/settings/landing-hero-image", formData, {
        ...authConfig(token),
        headers: {
          ...authConfig(token).headers,
          "Content-Type": "multipart/form-data",
        },
      });
      adminCache.delete("admin:settings");
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getEmailLogs(token) {
    return withAdminCache("admin:emails", async () => {
      try {
        const response = await client.get("/admin/email-logs", authConfig(token));
        return response.data;
      } catch (error) {
        return normalizeError(error);
      }
    });
  },
  async testEmail(token, recipient) {
    try {
      const response = await client.post("/admin/settings/test-email", { recipient }, authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async uploadFinalPaymentProof(token, bookingId, file) {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await client.post(`/admin/bookings/${bookingId}/final-payment-proof`, formData, {
        ...authConfig(token),
        headers: {
          ...authConfig(token).headers,
          "Content-Type": "multipart/form-data",
        },
      });
      bustAdminPrefix("admin:bookings:");
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getUsers(token) {
    try {
      const response = await client.get("/admin/users", authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async createUser(token, payload) {
    try {
      const response = await client.post("/admin/users", payload, authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async deleteUser(token, userId) {
    try {
      const response = await client.delete(`/admin/users/${userId}`, authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async changePassword(token, payload) {
    try {
      const response = await client.put("/auth/change-password", payload, authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
};

export const getProtectedDocumentUrl = (bookingId, documentType) => `${API_URL}/admin/documents/${bookingId}/${documentType}`;

export const fetchProtectedDocument = async (token, bookingId, documentType) => {
  const response = await fetch(getProtectedDocumentUrl(bookingId, documentType), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(errorPayload.detail || "Unable to open document.");
  }
  const contentType = response.headers.get("content-type") || "application/octet-stream";
  const disposition = response.headers.get("content-disposition") || "";
  const filenameMatch = disposition.match(/filename="?([^";\n]+)"?/);
  const filename = filenameMatch ? filenameMatch[1] : `document.${contentType.split("/")[1] || "bin"}`;
  const blob = await response.blob();
  const blobWithType = new Blob([blob], { type: contentType });
  const url = URL.createObjectURL(blobWithType);
  let type = "unsupported";
  if (contentType.startsWith("image/")) type = "image";
  else if (contentType === "application/pdf") type = "pdf";
  return { type, url, contentType, filename };
};

export const openProtectedDocument = async (token, bookingId, documentType) => {
  const result = await fetchProtectedDocument(token, bookingId, documentType);
  return result;
};