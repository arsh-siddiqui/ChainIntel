"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { HealthData } from "@/types";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: async () => (await api.get<HealthData>("/health")).data,
    refetchInterval: 30_000,
  });
}
