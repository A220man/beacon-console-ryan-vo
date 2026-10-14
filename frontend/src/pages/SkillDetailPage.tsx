import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, Skill } from "../api";
import { Button, Card, CardHeader, CardBody, Badge, LoadingSpinner, Alert } from "../components/ui";

interface SkillDetail extends Skill {
  schema: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export function SkillDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [skill, setSkill] = useState<SkillDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    if (!id) return;
    let mounted = true;
    api.getSkill(Number(id))
      .then((s) => {
        if (mounted) {
          setSkill({ ...s, schema: s.schema as Record<string, unknown>, metadata: s.metadata as Record<string, unknown> });
        }
      })
      .catch((err) => {
        if (mounted) {
          if (err.response?.status === 404) {
            setError("Skill not found");
          } else {
            setError("Failed to load skill");
          }
        }
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => { mounted = false; };
  }, [id]);

  const handleExecute = async () => {
    if (!skill) return;
    setExecuting(true);
    try {
      const execution = await api.createExecution({ skill_id: skill.id, input_params: {} });
      navigate(`/executions/${execution.id}`);
    } catch (err) {
      setError("Failed to start execution");
      console.error(err);
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center py-12"><LoadingSpinner size="lg" /></div>;
  }

  if (error || !skill) {
    return (
      <div className="max-w-3xl mx-auto">
        <Alert variant="danger">{error || "Skill not found"}</Alert>
        <Button variant="outline" onClick={() => navigate("/skills")} className="mt-4">
          Back to Skills
        </Button>
      </div>
    );
  }

  const getStatusVariant = (status: string) => {
    if (status === "validated") return "success";
    if (status === "draft") return "warning";
    return "danger";
  };

  const getCategoryVariant = (category: string) => {
    if (category === "genetics") return "primary";
    if (category === "onboarding") return "success";
    return "secondary";
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-[var(--color-text)]">{skill.display_name}</h1>
            <Badge variant={getStatusVariant(skill.status)}>{skill.status}</Badge>
            <Badge variant={getCategoryVariant(skill.category)}>{skill.category}</Badge>
          </div>
          <p className="text-[var(--color-text-muted)]">{skill.name} &bull; v{skill.version} &bull; by {skill.owner.username}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate("/skills")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mr-2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back
          </Button>
          <Button onClick={handleExecute} disabled={executing}>
            {executing ? (
              <>
                <LoadingSpinner size="sm" />
                Starting...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mr-2">
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
                Execute
              </>
            )}
          </Button>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Description</h2>
          </CardHeader>
          <CardBody>
            <p className="text-[var(--color-text)] whitespace-pre-wrap">{skill.description}</p>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Metadata</h2>
          </CardHeader>
          <CardBody>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-[var(--color-text-muted)]">Category</dt>
                <dd className="font-medium">{skill.category}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-[var(--color-text-muted)]">Status</dt>
                <dd className="font-medium">{skill.status}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-[var(--color-text-muted)]">Version</dt>
                <dd className="font-medium">{skill.version}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-[var(--color-text-muted)]">Owner</dt>
                <dd className="font-medium">{skill.owner.username}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-[var(--color-text-muted)]">Created</dt>
                <dd className="font-medium">{new Date(skill.created_at).toLocaleDateString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-[var(--color-text-muted)]">Updated</dt>
                <dd className="font-medium">{new Date(skill.updated_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Input Schema</h2>
        </CardHeader>
        <CardBody>
          <pre className="bg-[var(--color-bg)] p-4 rounded-md overflow-x-auto text-sm font-mono text-[var(--color-text)]">
            {JSON.stringify(skill.schema, null, 2)}
          </pre>
        </CardBody>
      </Card>

      {Object.keys(skill.metadata).length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Additional Metadata</h2>
          </CardHeader>
          <CardBody>
            <pre className="bg-[var(--color-bg)] p-4 rounded-md overflow-x-auto text-sm font-mono text-[var(--color-text)]">
              {JSON.stringify(skill.metadata, null, 2)}
            </pre>
          </CardBody>
        </Card>
      )}
    </div>
  );
}