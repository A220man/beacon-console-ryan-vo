import { useEffect, useState } from "react";
import { api } from "../api";
import { LoadingSpinner, Button } from "../components/ui";

export function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("error")) {
      setError(params.get("error") || "Authentication failed");
    }
  }, []);

  const handleLogin = async () => {
    setLoading(true);
    setError("");
    try {
      await api.login();
    } catch (err) {
      setError("Failed to initiate login");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-200px)] flex items-center justify-center px-4">
      <div className="card w-full max-w-md">
        <div className="card-header text-center">
          <svg className="mx-auto mb-4 text-[var(--color-primary)]" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M18 6a6 6 0 0 1 0 12H6a6 6 0 0 1 0-12h12z" />
            <path d="M12 6v12" />
            <path d="M6 12h12" />
          </svg>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">Beacon Console</h1>
          <p className="text-[var(--color-text-muted)] mt-1">AI Scientist Skills Platform</p>
        </div>
        <div className="card-body">
          {error && (
            <div className="alert alert-danger mb-4" role="alert">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0 mt-0.5">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-4">
            <div className="text-center text-[var(--color-text-muted)] text-sm">
              Sign in with your institutional account via Keycloak
            </div>
            <Button onClick={handleLogin} disabled={loading} className="w-full" size="lg">
              {loading ? (
                <>
                  <LoadingSpinner size="sm" />
                  Redirecting...
                </>
              ) : (
                <>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="2" y="2" width="20" height="20" rx="2" />
                    <path d="M12 6v12M6 12h12" />
                  </svg>
                  Sign in with Keycloak
                </>
              )}
            </Button>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--color-border)] text-center text-sm text-[var(--color-text-muted)]">
            <p>Beacon Console v1.0.0</p>
            <p className="mt-1">Ryan Vo <span>ryandtvo@gmail.com</span></p>
          </div>
        </div>
      </div>
    </div>
  );
}