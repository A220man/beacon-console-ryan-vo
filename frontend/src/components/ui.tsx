export function LoadingSpinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClass = size === "sm" ? "w-4 h-4 border-[1.5px]" : size === "lg" ? "w-8 h-8 border-3" : "w-6 h-6 border-2";
  return (
    <span className={`${sizeClass} rounded-full border-[var(--color-border)] border-t-[var(--color-primary)] animate-spin inline-block`} aria-hidden="true" />
  );
}

export function EmptyState({ icon, title, text, action }: { icon?: React.ReactNode; title: string; text: string; action?: React.ReactNode }) {
  return (
    <div className="empty-state">
      {icon && <div className="empty-state-icon">{icon}</div>}
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-text">{text}</p>
      {action && <div>{action}</div>}
    </div>
  );
}

export function Button({
  children,
  onClick,
  disabled = false,
  variant = "primary",
  size = "md",
  type = "button",
  className = "",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "outline" | "danger"; size?: "sm" | "md" | "lg" }) {
  const variantClass = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    outline: "btn-outline",
    danger: "btn-danger",
  }[variant];

  const sizeClass = {
    sm: "btn-sm",
    md: "",
    lg: "btn-lg",
  }[size];

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`btn ${variantClass} ${sizeClass} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function Badge({ children, variant = "secondary" }: { children: React.ReactNode; variant?: "primary" | "success" | "warning" | "danger" | "secondary" }) {
  const variantClass = {
    primary: "badge-primary",
    success: "badge-success",
    warning: "badge-warning",
    danger: "badge-danger",
    secondary: "badge-secondary",
  }[variant];

  return <span className={`badge ${variantClass}`}>{children}</span>;
}

export function Input({
  label,
  error,
  id,
  className = "",
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { label?: string; error?: string; id: string }) {
  return (
    <div className="w-full">
      {label && <label htmlFor={id} className="label">{label}</label>}
      <input
        id={id}
        className={`input ${error ? "input-error" : ""} ${className}`}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? `${id}-error` : undefined}
        {...props}
      />
      {error && <p id={`${id}-error`} className="mt-1 text-sm text-[var(--color-danger)]" role="alert">{error}</p>}
    </div>
  );
}

export function Textarea({
  label,
  error,
  id,
  className = "",
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string; error?: string; id: string }) {
  return (
    <div className="w-full">
      {label && <label htmlFor={id} className="label">{label}</label>}
      <textarea
        id={id}
        className={`input ${error ? "input-error" : ""} ${className}`}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? `${id}-error` : undefined}
        {...props}
      />
      {error && <p id={`${id}-error`} className="mt-1 text-sm text-[var(--color-danger)]" role="alert">{error}</p>}
    </div>
  );
}

export function Select({
  label,
  error,
  id,
  options,
  className = "",
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string; error?: string; id: string; options: { value: string; label: string }[] }) {
  return (
    <div className="w-full">
      {label && <label htmlFor={id} className="label">{label}</label>}
      <select
        id={id}
        className={`input ${error ? "input-error" : ""} ${className}`}
        aria-invalid={error ? "true" : "false"}
        aria-describedby={error ? `${id}-error` : undefined}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p id={`${id}-error`} className="mt-1 text-sm text-[var(--color-danger)]" role="alert">{error}</p>}
    </div>
  );
}

export function Card({ children, className = "", ...props }: React.HTMLAttributes<HTMLDivElement> & { className?: string }) {
  return <div className={`card ${className}`} {...props}>{children}</div>;
}

export function CardHeader({ children, className = "", ...props }: React.HTMLAttributes<HTMLDivElement> & { className?: string }) {
  return <div className={`card-header ${className}`} {...props}>{children}</div>;
}

export function CardBody({ children, className = "", ...props }: React.HTMLAttributes<HTMLDivElement> & { className?: string }) {
  return <div className={`card-body ${className}`} {...props}>{children}</div>;
}

export function CardFooter({ children, className = "", ...props }: React.HTMLAttributes<HTMLDivElement> & { className?: string }) {
  return <div className={`card-footer ${className}`} {...props}>{children}</div>;
}

export function Alert({ children, variant = "info", className = "", ...props }: React.HTMLAttributes<HTMLDivElement> & { variant?: "info" | "success" | "warning" | "danger"; className?: string }) {
  const variantClass = {
    info: "alert-info",
    success: "alert-success",
    warning: "alert-warning",
    danger: "alert-danger",
  }[variant];

  return (
    <div className={`alert ${variantClass} ${className}`} role="alert" {...props}>
      {children}
    </div>
  );
}

export function Table({ children, className = "", ...props }: React.HTMLAttributes<HTMLTableElement> & { className?: string }) {
  return (
    <div className="table-container">
      <table className={`table ${className}`} {...props}>{children}</table>
    </div>
  );
}