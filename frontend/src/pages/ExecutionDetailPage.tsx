import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, Execution } from "../api";
import { Button, Card, CardHeader, CardBody, Badge, LoadingSpinner, Alert } from "../components/ui";

interface ExecutionDetail extends Execution {
  input_params: Record<string, unknown>;
  output_result: Record<string, unknown> | null;
}

export function ExecutionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [execution, setExecution] = useState<ExecutionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!id) return;
    let mounted = true;
    api.getExecution(Number(id))
      .then((e) => {
        if (mounted) {
          setExecution({
            ...e,
            input_params: e.input_params as Record<string, unknown>,
            output_result: e.output_result as Record<string, unknown> | null,
          });
        }
      })
      .catch((err) => {
        if (mounted) {
          if (err.response?.status === 404) {
            setError("Execution not found");
          } else {
            setError("Failed to load execution");
          }
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => { mounted = false; };
  }, [id]);

  const handleRun = async () => {
    if (!execution) return;
    setRunning(true);
    try {
      const result = await api.runExecution(execution.id);
      setExecution({ ...execution, ...result, output_result: result.output_result as Record<string, unknown> | null });
    } catch (err) {
      setError("Failed to run execution");
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "completed": return "success";
      case "running": return "primary";
      case "pending": return "warning";
      case "failed": return "danger";
      case "cancelled": return "secondary";
      default: return "secondary";
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (error || !execution) {
    return (
      <div className="max-w-3xl mx-auto">
        <Alert variant="danger">{error || "Execution not found"}</Alert>
        <Button variant="outline" onClick={() => navigate("/executions")} className="mt-4">
          Back to Executions
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-[var(--color-text)]">Execution #{execution.id}</h1>
            <Badge variant={getStatusVariant(execution.status)}>{execution.status}</Badge>
          </div>
          <p className="text-[var(--color-text-muted)]">{execution.skill_name || `Skill #${execution.skill_id}`}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate("/executions")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mr-2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back
          </Button>
          {execution.status === "pending" || execution.status === "failed" ? (
            <Button onClick={handleRun} disabled={running}>
              {running ? (
                <>
                  <LoadingSpinner size="sm" />
                  Running...
                </>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mr-2">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                  Run
                </>
              )}
            </Button>
          ) : null}
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Input Parameters</h2>
          </CardHeader>
          <CardBody>
            {Object.keys(execution.input_params).length > 0 ? (
              <pre className="bg-[var(--color-bg)] p-4 rounded-md overflow-x-auto text-sm font-mono text-[var(--color-text)]">
                {JSON.stringify(execution.input_params, null, 2)}
              </pre>
            ) : (
              <p className="text-[var(--color-text-muted)]">No input parameters</p>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Output Result</h2>
          </CardHeader>
          <CardBody>
            {execution.output_result ? (
              <pre className="bg-[var(--color-bg)] p-4 rounded-md overflow-x-auto text-sm font-mono text-[var(--color-text)]">
                {JSON.stringify(execution.output_result, null, 2)}
              </pre>
            ) : execution.error_message ? (
              <Alert variant="danger">
                <pre className="text-sm font-mono">{execution.error_message}</pre>
              </Alert>
            ) : (
              <p className="text-[var(--color-text-muted)]">No output yet</p>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Execution Timeline</h2>
        </CardHeader>
        <CardBody>
          <dl className="space-y-3 text-sm">
            <div className="flex flex-col sm:flex-row sm:justify-between gap-1">
              <dt className="text-[var(--color-text-muted)]">Created</dt>
              <dd className="font-medium">{new Date(execution.created_at).toLocaleString()}</dd>
            </div>
            <div className="flex flex-col sm:flex-row sm:justify-between gap-1">
              <dt className="text-[var(--color-text-muted)]">Started</dt>
              <dd className="font-medium">{execution.started_at ? new Date(execution.started_at).toLocaleString() : "—"}</dd>
            </div>
            <div className="flex flex-col sm:flex-row sm:justify-between gap-1">
              <dt className="text-[var(--color-text-muted)]">Completed</dt>
              <dd className="font-medium">{execution.completed_at ? new Date(execution.completed_at).toLocaleString() : "—"}</dd>
            </div>
            {execution.started_at && execution.completed_at && (
              <div className="flex flex-col sm:flex-row sm:justify-between gap-1">
                <dt className="text-[var(--color-text-muted)]">Duration</dt>
                <dd className="font-medium">
                  {((new Date(execution.completed_at).getTime() - new Date(execution.started_at).getTime()) / 1000).toFixed(2)}s
                </dd>
              </div>
            )}
          </dl>
        </CardBody>
      </Card>
    </div>
  );
}