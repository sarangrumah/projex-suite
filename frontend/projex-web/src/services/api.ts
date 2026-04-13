import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      try {
        const refresh = localStorage.getItem("refresh_token");
        const { data } = await axios.post("/api/v1/auth/refresh", {
          refresh_token: refresh,
        });
        localStorage.setItem("access_token", data.data.access_token);
        error.config.headers.Authorization = `Bearer ${data.data.access_token}`;
        return axios(error.config);
      } catch {
        localStorage.clear();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);
