import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, Execution, PaginatedResponse } from "../api";
import { Button, Card, CardHeader, CardBody, Table, Badge, EmptyState, LoadingSpinner, Alert, Select } from "../components/ui";

export function ExecutionsPage() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const params = new URLSearchParams(searchParams);
    setPage(Number(params.get("page")) || 1);
    setStatusFilter(params.get("status") || "");
  }, [searchParams]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (page > 1) params.set("page", String(page));
    if (statusFilter) params.set("status", statusFilter);
    setSearchParams(params, { replace: true });
  }, [page, statusFilter, setSearchParams]);

  const fetchExecutions = async () => {
    setLoading(true);
    setError("");
    try {
      const response: PaginatedResponse<Execution> = await api.getExecutions({
        page,
        page_size: pageSize,
        status: statusFilter || undefined,
      });
      setExecutions(response.items);
      setTotal(response.total);
    } catch (err) {
      setError("Failed to load executions");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutions();
  }, [page, statusFilter]);

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

  const statuses = [
    { value: "", label: "All Statuses" },
    { value: "pending", label: "Pending" },
    { value: "running", label: "Running" },
    { value: "completed", label: "Completed" },
    { value: "failed", label: "Failed" },
    { value: "cancelled", label: "Cancelled" },
  ];

  if (loading && executions.length === 0) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text)]">Executions</h1>
        <p className="text-[var(--color-text-muted)]">Monitor and manage skill executions</p>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Card>
        <CardHeader>
          <div className="flex flex-wrap gap-3">
            <Select
              id="status-filter"
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              options={statuses}
              aria-label="Filter by status"
              className="w-auto min-w-[180px]"
            />
          </div>
        </CardHeader>
        <CardBody className="p-0">
          {executions.length === 0 ? (
            <EmptyState
              title="No executions found"
              text={statusFilter ? `No executions with status "${statuses.find(s => s.value === statusFilter)?.label}"` : "Start an execution from a skill detail page."}
            />
          ) : (
            <>
              <Table>
                <thead>
                  <tr>
                    <th className="w-[60px]">ID</th>
                    <th>Skill</th>
                    <th className="hidden md:table-cell">Status</th>
                    <th className="hidden lg:table-cell">Started</th>
                    <th className="hidden lg:table-cell">Completed</th>
                    <th className="w-[100px] text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.map((exec) => (
                    <tr key={exec.id}>
                      <td className="font-mono text-sm text-[var(--color-text-muted)]">#{exec.id}</td>
                      <td>
                        <Link to={`/executions/${exec.id}`} className="font-medium text-[var(--color-text)] hover:text-[var(--color-primary)]">
                          {exec.skill_name || `Skill #${exec.skill_id}`}
                        </Link>
                      </td>
                      <td className="hidden md:table-cell">
                        <Badge variant={getStatusVariant(exec.status)}>{exec.status}</Badge>
                      </td>
                      <td className="hidden lg:table-cell text-[var(--color-text-muted)] text-sm">
                        {exec.started_at ? new Date(exec.started_at).toLocaleString() : "—"}
                      </td>
                      <td className="hidden lg:table-cell text-[var(--color-text-muted)] text-sm">
                        {exec.completed_at ? new Date(exec.completed_at).toLocaleString() : "—"}
                      </td>
                      <td className="text-right">
                        <Link to={`/executions/${exec.id}`} className="btn btn-outline btn-sm">
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>

              {total > pageSize && (
                <div className="card-footer flex items-center justify-between">
                  <div className="text-sm text-[var(--color-text-muted)]">
                    Showing {Math.min((page - 1) * pageSize + 1, total)} to {Math.min(page * pageSize, total)} of {total} results
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => setPage(p => p - 1)} disabled={page <= 1}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page * pageSize >= total}>
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardBody>
      </Card>
    </div>
  );
}