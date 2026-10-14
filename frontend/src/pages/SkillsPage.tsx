import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, Skill, PaginatedResponse } from "../api";
import { Button } from "../components/ui";
import { Card, CardHeader, CardBody, Table, Badge, EmptyState, Input, Select, LoadingSpinner, Alert } from "../components/ui";

export function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const params = new URLSearchParams(searchParams);
    setPage(Number(params.get("page")) || 1);
    setSearch(params.get("search") || "");
    setCategoryFilter(params.get("category") || "");
    setStatusFilter(params.get("status") || "");
  }, [searchParams]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (page > 1) params.set("page", String(page));
    if (search) params.set("search", search);
    if (categoryFilter) params.set("category", categoryFilter);
    if (statusFilter) params.set("status", statusFilter);
    setSearchParams(params, { replace: true });
  }, [page, search, categoryFilter, statusFilter, setSearchParams]);

  const fetchSkills = async () => {
    setLoading(true);
    setError("");
    try {
      const response: PaginatedResponse<Skill> = await api.getSkills({
        page,
        page_size: pageSize,
        search: search || undefined,
        category: categoryFilter || undefined,
        status: statusFilter || undefined,
      });
      setSkills(response.items);
      setTotal(response.total);
    } catch (err) {
      setError("Failed to load skills");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSkills();
  }, [page, search, categoryFilter, statusFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  const categories = [
    { value: "", label: "All Categories" },
    { value: "genetics", label: "Genetics" },
    { value: "ontology", label: "Ontology" },
    { value: "literature", label: "Literature" },
    { value: "analysis", label: "Analysis" },
    { value: "onboarding", label: "Onboarding" },
    { value: "other", label: "Other" },
  ];

  const statuses = [
    { value: "", label: "All Statuses" },
    { value: "draft", label: "Draft" },
    { value: "validated", label: "Validated" },
    { value: "deprecated", label: "Deprecated" },
  ];

  if (loading && skills.length === 0) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">Skills</h1>
          <p className="text-[var(--color-text-muted)]">Browse and manage validated scientific agent skills</p>
        </div>
        <Link to="/skills/new">
          <Button>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mr-2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New Skill
          </Button>
        </Link>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Card>
        <CardHeader>
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 min-w-[200px]">
              <Input
                id="search"
                placeholder="Search skills..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                aria-label="Search skills"
              />
            </div>
            <div className="flex gap-2 sm:hidden">
              <Select
                id="category"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                options={categories}
                aria-label="Filter by category"
              />
              <Select
                id="status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                options={statuses}
                aria-label="Filter by status"
              />
            </div>
          </form>
        </CardHeader>
        <CardBody className="p-0">
          {skills.length === 0 ? (
            <EmptyState
              title="No skills found"
              text="Try adjusting your search or filters, or create a new skill."
              action={<Button variant="outline" onClick={() => { setSearch(""); setCategoryFilter(""); setStatusFilter(""); }}>Clear filters</Button>}
            />
          ) : (
            <>
              <Table>
                <thead>
                  <tr>
                    <th className="w-[40%]">Name</th>
                    <th className="hidden md:table-cell">Category</th>
                    <th className="hidden lg:table-cell">Status</th>
                    <th className="hidden xl:table-cell">Version</th>
                    <th className="hidden md:table-cell">Owner</th>
                    <th className="w-[100px] text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {skills.map((skill) => (
                    <tr key={skill.id}>
                      <td>
                        <Link to={`/skills/${skill.id}`} className="font-medium text-[var(--color-text)] hover:text-[var(--color-primary)]">
                          {skill.display_name}
                        </Link>
                        <div className="text-xs text-[var(--color-text-muted)]">{skill.name}</div>
                      </td>
                      <td className="hidden md:table-cell">
                        <Badge variant={skill.category === "genetics" ? "primary" : skill.category === "onboarding" ? "success" : "secondary"}>
                          {skill.category}
                        </Badge>
                      </td>
                      <td className="hidden lg:table-cell">
                        <Badge variant={skill.status === "validated" ? "success" : skill.status === "draft" ? "warning" : "danger"}>
                          {skill.status}
                        </Badge>
                      </td>
                      <td className="hidden xl:table-cell text-[var(--color-text-muted)]">{skill.version}</td>
                      <td className="hidden md:table-cell text-[var(--color-text-muted)]">{skill.owner.username}</td>
                      <td className="text-right">
                        <Link to={`/skills/${skill.id}`} className="btn btn-outline btn-sm">
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

      <div className="hidden sm:block">
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <Button
              key={cat.value}
              variant={categoryFilter === cat.value ? "primary" : "outline"}
              size="sm"
              onClick={() => { setCategoryFilter(cat.value); setPage(1); }}
            >
              {cat.label}
            </Button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {statuses.map((st) => (
            <Button
              key={st.value}
              variant={statusFilter === st.value ? "primary" : "outline"}
              size="sm"
              onClick={() => { setStatusFilter(st.value); setPage(1); }}
            >
              {st.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}