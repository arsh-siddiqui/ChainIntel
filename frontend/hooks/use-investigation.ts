"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { InvestigationBundle } from "@/types";

export const PIPELINE_STEPS = [
  "Validating wallet",
  "Detecting blockchain",
  "Fetching blockchain data",
  "Analyzing transactions",
  "Checking threat intelligence",
  "Correlating OSINT",
  "Building graph",
  "Calculating indicators",
  "Completed",
];

export function useInvestigation() {
  const queryClient = useQueryClient();
  const [progressStep, setProgressStep] = useState(-1);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const mutation = useMutation({
    mutationFn: async (input: { address: string; blockchain: string }): Promise<InvestigationBundle> => {
      const { data } = await api.post<InvestigationBundle>("/wallets/investigate", input);
      return data;
    },
    onMutate: () => {
      setProgressStep(0);
      stopTimer();
      timerRef.current = setInterval(() => {
        setProgressStep((step) => Math.min(step + 1, PIPELINE_STEPS.length - 2));
      }, 120);
    },
    onSuccess: () => {
      stopTimer();
      setProgressStep(PIPELINE_STEPS.length - 1);
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["health"] });
    },
    onError: () => {
      stopTimer();
      setProgressStep(-1);
    },
  });

  useEffect(() => stopTimer, []);

  return {
    investigate: mutation.mutate,
    investigateAsync: mutation.mutateAsync,
    isLoading: mutation.isPending,
    error: mutation.error as ApiErrorLike | null,
    result: mutation.data ?? null,
    reset: mutation.reset,
    progressStep,
  };
}

interface ApiErrorLike {
  code: string;
  message: string;
  status: number;
}
