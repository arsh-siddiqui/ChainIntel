"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { Button } from "@/components/common/ui";

export function CopyButton({ value, label }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <Button variant="ghost" size="sm" onClick={copy} aria-label={label ?? "Copy to clipboard"} title={label ?? "Copy to clipboard"}>
      {copied ? <Check size={13} className="text-emerald-600" /> : <Copy size={13} />}
    </Button>
  );
}
