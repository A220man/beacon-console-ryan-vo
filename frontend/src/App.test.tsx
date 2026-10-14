import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";

const { mockUser, mockSkills, mockExecutions, mockHealth } = vi.hoisted(() => ({
  mockUser: {
    id: 1,
    username: "testuser",
    email: "test@example.com",
    full_name: "Test User",
    role: "operator",
    is_active: true,
  },
  mockSkills: {
    items: [
      { id: 1, name: "locus-compare", display_name: "Locus Compare", description: "Generate locus compare plots", category: "genetics", status: "validated", version: "1.0.0", schema: {}, metadata: {}, owner: { id: 1, username: "testuser" }, created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z" },
    ],
    total: 1,
    page: 1,
    page_size: 20,
    total_pages: 1,
  },
  mockExecutions: {
    items: [
      { id: 1, skill_id: 1, skill_name: "Locus Compare", status: "completed", input_params: {}, output_result: { result: "ok" }, error_message: null, started_at: "2026-01-01T00:00:00Z", completed_at: "2026-01-01T00:00:01Z", created_at: "2026-01-01T00:00:00Z" },
    ],
    total: 1,
    page: 1,
    page_size: 20,
    total_pages: 1,
  },
  mockHealth: { status: "ok", service: "beacon-console", version: "1.0.0", environment: "development" },
}));

vi.mock("./api", () => ({
  api: {
    getCurrentUser: vi.fn().mockResolvedValue(mockUser),
    getSkills: vi.fn().mockResolvedValue(mockSkills),
    getExecutions: vi.fn().mockResolvedValue(mockExecutions),
    createExecution: vi.fn(),
    runExecution: vi.fn(),
    healthCheck: vi.fn().mockResolvedValue(mockHealth),
  },
}));

import { api } from "./api";

function renderApp() {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
}

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.getCurrentUser.mockResolvedValue(mockUser);
    api.getSkills.mockResolvedValue(mockSkills);
    api.getExecutions.mockResolvedValue(mockExecutions);
    api.healthCheck.mockResolvedValue(mockHealth);
  });

  it("renders login page when not authenticated", async () => {
    api.getCurrentUser.mockRejectedValue(new Error("Unauthorized"));
    renderApp();
    await waitFor(() => {
      expect(screen.getByText("Sign in with Keycloak")).toBeInTheDocument();
    });
  });

  it("renders skills page when authenticated", async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByText("Locus Compare")).toBeInTheDocument();
    });
  });

  it("shows navigation for authenticated user", async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByText("Skills")).toBeInTheDocument();
      expect(screen.getByText("Executions")).toBeInTheDocument();
      expect(screen.getByText("Settings")).toBeInTheDocument();
    });
  });

  it("navigates to executions page", async () => {
    renderApp();
    await waitFor(() => {
      fireEvent.click(screen.getByText("Executions"));
    });
    await waitFor(() => {
      expect(screen.getByText("#1")).toBeInTheDocument();
    });
  });
});

describe("UI Components", () => {
  it("renders Button with correct variant", async () => {
    const { Button } = await import("./components/ui");
    
    render(<Button variant="primary">Click me</Button>);
    expect(screen.getByRole("button", { name: "Click me" })).toHaveClass("btn-primary");
  });

  it("renders Badge with correct variant", async () => {
    const { Badge } = await import("./components/ui");
    
    render(<Badge variant="success">Success</Badge>);
    expect(screen.getByText("Success")).toHaveClass("badge-success");
  });

  it("renders Alert with correct variant", async () => {
    const { Alert } = await import("./components/ui");
    
    render(<Alert variant="danger">Error message</Alert>);
    expect(screen.getByText("Error message")).toHaveClass("alert-danger");
  });
});