import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

class ApiClient {
  private client: AxiosInstance;
  private csrfToken: string | null = null;
  private refreshPromise: Promise<void> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      withCredentials: true,
      headers: {
        "Content-Type": "application/json",
      },
      timeout: 30000,
    });

    this.client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
      if (this.csrfToken && ["post", "put", "patch", "delete"].includes(config.method || "")) {
        config.headers["X-CSRF-Token"] = this.csrfToken;
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          if (!this.refreshPromise) {
            this.refreshPromise = this.refreshCsrfToken();
          }

          try {
            await this.refreshPromise;
            this.refreshPromise = null;

            if (this.csrfToken) {
              originalRequest.headers["X-CSRF-Token"] = this.csrfToken;
            }
            return this.client(originalRequest);
          } catch {
            this.refreshPromise = null;
            this.clearAuth();
            window.location.href = "/login";
            return Promise.reject(error);
          }
        }

        if (error.response?.status === 403) {
          this.clearAuth();
        }

        return Promise.reject(error);
      }
    );
  }

  setCsrfToken(token: string) {
    this.csrfToken = token;
  }

  clearAuth() {
    this.csrfToken = null;
  }

  private async refreshCsrfToken(): Promise<void> {
    try {
      const response = await this.client.get("/auth/csrf");
      this.csrfToken = response.data.csrf_token;
    } catch {
      throw new Error("Failed to refresh CSRF token");
    }
  }

  async login(): Promise<void> {
    window.location.href = `${API_BASE_URL}/auth/login`;
  }

  async logout(): Promise<void> {
    await this.client.post("/auth/logout");
    this.clearAuth();
    window.location.href = "/";
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get("/auth/me");
    return response.data;
  }

  async getSkills(params?: {
    category?: string;
    status?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Skill>> {
    const response = await this.client.get("/skills", { params });
    return response.data;
  }

  async getSkill(id: number): Promise<Skill> {
    const response = await this.client.get(`/skills/${id}`);
    return response.data;
  }

  async createSkill(data: CreateSkillRequest): Promise<Skill> {
    const response = await this.client.post("/skills", data);
    return response.data;
  }

  async updateSkill(id: number, data: UpdateSkillRequest): Promise<Skill> {
    const response = await this.client.patch(`/skills/${id}`, data);
    return response.data;
  }

  async deleteSkill(id: number): Promise<void> {
    await this.client.delete(`/skills/${id}`);
  }

  async getExecutions(params?: {
    skill_id?: number;
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Execution>> {
    const response = await this.client.get("/executions", { params });
    return response.data;
  }

  async getExecution(id: number): Promise<Execution> {
    const response = await this.client.get(`/executions/${id}`);
    return response.data;
  }

  async createExecution(data: CreateExecutionRequest): Promise<Execution> {
    const response = await this.client.post("/executions", data);
    return response.data;
  }

  async runExecution(id: number): Promise<Execution> {
    const response = await this.client.post(`/executions/${id}/run`);
    return response.data;
  }

  async explainExecution(id: number): Promise<ExplanationResponse> {
    const response = await this.client.post(`/executions/${id}/explain`);
    return response.data;
  }

  async healthCheck(): Promise<HealthResponse> {
    const response = await this.client.get("/health");
    return response.data;
  }
}


export interface ExplanationResponse {
  execution_id: number;
  explanation: {
    status: "completed" | "skipped" | "error";
    content?: string;
    reason?: string;
    provider?: string;
    model?: string;
    advisory: boolean;
    usage?: Record<string, unknown>;
  };
}

export const api = new ApiClient();

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: "viewer" | "operator" | "admin";
  is_active: boolean;
}

export interface Skill {
  id: number;
  name: string;
  display_name: string;
  description: string;
  category: "genetics" | "ontology" | "literature" | "analysis" | "onboarding" | "other";
  status: "draft" | "validated" | "deprecated";
  version: string;
  schema: Record<string, unknown>;
  metadata: Record<string, unknown>;
  owner: { id: number; username: string };
  created_at: string;
  updated_at: string;
}

export interface CreateSkillRequest {
  name: string;
  display_name: string;
  description: string;
  category?: string;
  status?: string;
  version?: string;
  schema: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface UpdateSkillRequest {
  name?: string;
  display_name?: string;
  description?: string;
  category?: string;
  status?: string;
  version?: string;
  schema?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface Execution {
  id: number;
  skill_id: number;
  skill_name: string | null;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  input_params: Record<string, unknown>;
  output_result: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface CreateExecutionRequest {
  skill_id: number;
  input_params?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  database?: string;
}