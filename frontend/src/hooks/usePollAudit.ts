import { useEffect, useState } from "react";

import { apiFetch } from "./useApi";
import type { AuditDetail } from "../utils/types";

export function usePollAudit(auditId: string | undefined) {
  const [audit, setAudit] = useState<AuditDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!auditId) {
      return;
    }

    let active = true;
    let timer: number | undefined;

    const load = async () => {
      try {
        const data = await apiFetch<AuditDetail>(`/audits/${auditId}`);
        if (!active) {
          return;
        }
        setAudit(data);
        setError(null);
        if (data.status === "queued" || data.status === "processing") {
          timer = window.setTimeout(load, 5000);
        }
      } catch (err) {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : "Failed to load audit");
      }
    };

    void load();

    return () => {
      active = false;
      if (timer) {
        window.clearTimeout(timer);
      }
    };
  }, [auditId]);

  return { audit, error };
}
