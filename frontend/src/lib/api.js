import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_URL = `${BACKEND_URL}/api`;

const client = axios.create({
  baseURL: API_URL,
  timeout: 15000,
});

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
    try {
      const response = await client.get("/public/config");
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getPrograms() {
    try {
      const response = await client.get("/public/programs");
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
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
    try {
      const response = await client.get("/admin/dashboard", authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getBookings(token) {
    try {
      const response = await client.get("/admin/bookings", authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async updateBooking(token, bookingId, payload) {
    try {
      const response = await client.patch(`/admin/bookings/${bookingId}`, payload, authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async createManualBooking(token, payload) {
    try {
      const response = await client.post("/admin/bookings/manual", payload, authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getPrograms(token) {
    try {
      const response = await client.get("/admin/programs", authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async createProgram(token, payload) {
    try {
      const response = await client.post("/admin/programs", payload, authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async updateProgram(token, programId, payload) {
    try {
      const response = await client.put(`/admin/programs/${programId}`, payload, authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getCapacity(token) {
    try {
      const response = await client.get("/admin/capacity", authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async updateCapacity(token, weekStart, capacity) {
    try {
      const response = await client.put(`/admin/capacity/${weekStart}`, { capacity }, authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getSettings(token) {
    try {
      const response = await client.get("/admin/settings", authConfig(token));
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async updateSettings(token, payload) {
    try {
      const response = await client.put("/admin/settings", payload, authConfig(token));
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
      return response.data;
    } catch (error) {
      return normalizeError(error);
    }
  },
  async getEmailLogs(token) {
    try {
      const response = await client.get("/admin/email-logs", authConfig(token));
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