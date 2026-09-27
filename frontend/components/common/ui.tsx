"use client";

import clsx from "clsx";
import { motion, type HTMLMotionProps } from "framer-motion";
import { forwardRef, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes } from "react";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={clsx(
        "rounded-2xl border transition-all duration-200",
        "border-slate-200/90 bg-white/95 text-slate-900 shadow-[0_1px_3px_rgba(15,23,42,0.04),0_8px_24px_-4px_rgba(15,23,42,0.05)]",
        "dark:border-slate-800/80 dark:bg-slate-900/75 dark:text-slate-100 dark:shadow-2xl dark:shadow-black/50 backdrop-blur-xl",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action }: { title: ReactNode; subtitle?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b px-6 py-4 border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/40 rounded-t-2xl">
      <div>
        <h3 className="text-sm font-semibold tracking-tight text-slate-900 dark:text-slate-100">{title}</h3>
        {subtitle ? <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function Badge({ children, className, title }: { children: ReactNode; className?: string; title?: string }) {
  return (
    <span
      title={title}
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-0.5 text-[11px] font-semibold tracking-wide backdrop-blur-sm transition-colors",
        className ?? "border-slate-200 bg-slate-100/80 text-slate-700 dark:border-slate-700/80 dark:bg-slate-800/60 dark:text-slate-300",
      )}
    >
      {children}
    </span>
  );
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
};

export function Button({ variant = "primary", size = "md", className, disabled, children, ...props }: ButtonProps) {
  return (
    <motion.button
      whileHover={disabled ? undefined : { y: -1 }}
      whileTap={disabled ? undefined : { scale: 0.98 }}
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-xl font-semibold tracking-tight transition-all duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-500 disabled:cursor-not-allowed disabled:opacity-40",
        size === "sm" ? "px-3 py-1.5 text-xs" : "px-4 py-2.5 text-sm",
        variant === "primary" &&
          "bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 text-white shadow-md shadow-sky-500/20 hover:from-sky-400 hover:to-indigo-500 hover:shadow-lg hover:shadow-sky-500/30",
        variant === "secondary" &&
          "border border-slate-200 bg-white/90 text-slate-700 hover:bg-slate-50 hover:text-slate-900 shadow-sm dark:border-slate-700/80 dark:bg-slate-800/80 dark:text-slate-200 dark:hover:bg-slate-700/80 dark:hover:text-white dark:hover:border-slate-600 backdrop-blur-md",
        variant === "ghost" && "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-slate-100",
        variant === "danger" &&
          "bg-gradient-to-r from-rose-600 to-red-600 text-white shadow-md shadow-rose-500/20 hover:from-rose-500 hover:to-red-500 hover:shadow-lg hover:shadow-rose-500/30",
        className,
      )}
      disabled={disabled}
      {...(props as HTMLMotionProps<"button">)}
    >
      {children}
    </motion.button>
  );
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input({ className, ...props }, ref) {
  return (
    <input
      ref={ref}
      className={clsx(
        "w-full rounded-xl border px-3.5 py-2.5 text-sm shadow-sm transition-all focus:outline-none focus:ring-2",
        "border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:ring-sky-500/20",
        "dark:border-slate-700/80 dark:bg-slate-950/70 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-cyan-400 dark:focus:ring-cyan-500/20",
        className,
      )}
      {...props}
    />
  );
});

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(function Select({ className, ...props }, ref) {
  return (
    <select
      ref={ref}
      className={clsx(
        "rounded-xl border px-3.5 py-2.5 text-sm shadow-sm transition-all focus:outline-none focus:ring-2",
        "border-slate-200 bg-white text-slate-900 focus:border-sky-500 focus:ring-sky-500/20",
        "dark:border-slate-700/80 dark:bg-slate-950/70 dark:text-slate-100 dark:focus:border-cyan-400 dark:focus:ring-cyan-500/20",
        className,
      )}
      {...props}
    />
  );
});

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={clsx(
        "inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-sky-600 dark:border-slate-700 dark:border-t-cyan-400",
        className,
      )}
    />
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("animate-pulse rounded-lg bg-slate-200/70 dark:bg-slate-800/60", className)} />;
}

interface TextareaLikeProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  ariaLabel?: string;
  rows?: number;
}

export function TextareaLike({ value, onChange, placeholder, ariaLabel, rows = 3 }: TextareaLikeProps) {
  return (
    <textarea
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
      aria-label={ariaLabel}
      rows={rows}
      className={clsx(
        "w-full rounded-xl border px-3.5 py-2.5 text-sm shadow-sm transition-all focus:outline-none focus:ring-2",
        "border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:ring-sky-500/20",
        "dark:border-slate-700/80 dark:bg-slate-950/70 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-cyan-400 dark:focus:ring-cyan-500/20",
      )}
    />
  );
}

export function EmptyState({ icon, title, description, action }: { icon?: ReactNode; title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-6 py-12 text-center">
      {icon ? <div className="text-slate-400 dark:text-slate-600">{icon}</div> : null}
      <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{title}</p>
      {description ? <p className="max-w-md text-xs text-slate-500 dark:text-slate-400">{description}</p> : null}
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 px-6 py-10 text-center">
      <p className="max-w-md text-sm font-semibold text-rose-600 dark:text-rose-400">{message}</p>
      {onRetry ? (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
