import { useEffect, useState } from "react";
import { api, User, HealthResponse } from "../api";
import { Card, CardHeader, CardBody, LoadingSpinner } from "../components/ui";

export function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    Promise.all([api.getCurrentUser(), api.healthCheck()])
      .then(([u, h]) => {
        if (mounted) {
          setUser(u);
          setHealth(h);
        }
      })
      .catch(() => {
        if (mounted) setLoading(false);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => { mounted = false; };
  }, []);

  if (loading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-[var(--color-text)]">Settings</h1>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Account</h2>
        </CardHeader>
        <CardBody>
          {user && (
            <dl className="space-y-4">
              <div className="grid sm:grid-cols-[140px_1fr] gap-4 items-center">
                <dt className="text-[var(--color-text-muted)]">Username</dt>
                <dd className="font-medium">{user.username}</dd>
              </div>
              <div className="grid sm:grid-cols-[140px_1fr] gap-4 items-center">
                <dt className="text-[var(--color-text-muted)]">Email</dt>
                <dd>{user.email}</dd>
              </div>
              <div className="grid sm:grid-cols-[140px_1fr] gap-4 items-center">
                <dt className="text-[var(--color-text-muted)]">Full Name</dt>
                <dd>{user.full_name || "—"}</dd>
              </div>
              <div className="grid sm:grid-cols-[140px_1fr] gap-4 items-center">
                <dt className="text-[var(--color-text-muted)]">Role</dt>
                <dd>
                  <span className="badge badge-secondary">{user.role}</span>
                </dd>
              </div>
              <div className="grid sm:grid-cols-[140px_1fr] gap-4 items-center">
                <dt className="text-[var(--color-text-muted)]">Status</dt>
                <dd>
                  <span className={user.is_active ? "badge badge-success" : "badge badge-danger"}>
                    {user.is_active ? "Active" : "Inactive"}
                  </span>
                </dd>
              </div>
            </dl>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">System Health</h2>
        </CardHeader>
        <CardBody>
          {health && (
            <dl className="space-y-3">
              <div className="grid sm:grid-cols-[140px_1fr] gap-4 items-center">
                <dt className="text-[var(--color-text-muted)]">Service</dt>
                <dd className="font-medium">{health.service}</dd>
              </div>
              <div className="grid sm:grid-cols-[140px_1fr] gap-4 items-center">
                <dt className="text-[var(--color-text-muted)]">Version</dt>
                <dd className="font-medium">{health.version}</dd>
              </div>
              <div className="grid sm:grid-cols-[140px_1fr] gap-4 items-center">
                <dt className="text-[var(--color-text-muted)]">Environment</dt>
                <dd>
                  <span className={health.environment === "production" ? "badge badge-primary" : "badge badge-warning"}>
                    {health.environment}
                  </span>
                </dd>
              </div>
              <div className="grid sm:grid-cols-[140px_1fr] gap-4 items-center">
                <dt className="text-[var(--color-text-muted)]">Status</dt>
                <dd>
                  <span className={health.status === "ok" ? "badge badge-success" : "badge badge-danger"}>
                    {health.status}
                  </span>
                </dd>
              </div>
              {health.database && (
                <div className="grid sm:grid-cols-[140px_1fr] gap-4 items-center">
                  <dt className="text-[var(--color-text-muted)]">Database</dt>
                  <dd>
                    <span className={health.database === "connected" ? "badge badge-success" : "badge badge-danger"}>
                      {health.database}
                    </span>
                  </dd>
                </div>
              )}
            </dl>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Configuration</h2>
        </CardHeader>
        <CardBody>
          <p className="text-[var(--color-text-muted)] text-sm mb-4">
            These settings are configured via environment variables. See <code>.env.example</code> for available options.
          </p>
          <div className="space-y-3 text-sm font-mono bg-[var(--color-bg)] p-4 rounded-md">
            <div>API Base URL: <span className="text-[var(--color-primary)]">{import.meta.env.VITE_API_BASE_URL || "/api"}</span></div>
            <div>App Version: <span className="text-[var(--color-primary)]">{health?.version || "1.0.0"}</span></div>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">About</h2>
        </CardHeader>
        <CardBody>
          <div className="space-y-2 text-sm">
            <p><strong>Beacon Console</strong> — AI Scientist Skills Platform</p>
            <p>Version: {health?.version || "1.0.0"}</p>
            <p>Author: Ryan Vo <span>ryandtvo@gmail.com</span></p>
            <p className="text-[var(--color-text-muted)]">
              A console for browsing, configuring, and executing validated scientific agent skills.
              Supports statistical genetics workflows and field onboarding guided learning.
            </p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}