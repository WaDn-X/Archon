import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { STALE_TIMES } from "@/features/shared/config/queryPatterns";
import { allowlistService } from "../services/allowlistService";
import type { AllowlistEntry, AllowlistSection } from "../types";

export const allowlistKeys = {
  all: ["allowlist"] as const,
  config: () => [...allowlistKeys.all, "config"] as const,
  discovered: () => [...allowlistKeys.all, "discovered"] as const,
};

export function useAllowlist() {
  return useQuery({
    queryKey: allowlistKeys.config(),
    queryFn: () => allowlistService.getAllowlist(),
    staleTime: STALE_TIMES.rare,
  });
}

export function useDiscoveredPlugins() {
  return useQuery({
    queryKey: allowlistKeys.discovered(),
    queryFn: () => allowlistService.getDiscoveredPlugins(),
    staleTime: STALE_TIMES.rare,
  });
}

export function useAllowlistMutations() {
  const queryClient = useQueryClient();

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: allowlistKeys.all });
  };

  const addEntry = useMutation({
    mutationFn: ({ section, entry }: { section: AllowlistSection; entry: AllowlistEntry }) =>
      allowlistService.addEntry(section, entry),
    onSuccess: invalidate,
  });

  const removeEntry = useMutation({
    mutationFn: ({ section, name }: { section: AllowlistSection; name: string }) =>
      allowlistService.removeEntry(section, name),
    onSuccess: invalidate,
  });

  const setEntryEnabled = useMutation({
    mutationFn: ({ section, name, enabled }: { section: AllowlistSection; name: string; enabled: boolean }) =>
      allowlistService.setEntryEnabled(section, name, enabled),
    onSuccess: invalidate,
  });

  return {
    addEntry,
    removeEntry,
    setEntryEnabled,
    isPending: addEntry.isPending || removeEntry.isPending || setEntryEnabled.isPending,
  };
}
