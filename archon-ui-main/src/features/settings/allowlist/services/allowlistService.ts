import { callAPIWithETag } from "@/features/shared/api/apiClient";
import { APIServiceError } from "@/features/shared/types/errors";
import type { AllowlistEntry, AllowlistEntryActionRequest, AllowlistFile, AllowlistSection } from "../types";

const ALLOWLIST_ENDPOINT = "/api/plugins/allowlist";
const DISCOVERED_ENDPOINT = "/api/plugins/discovered";

export const ALLOWLIST_WRITE_FORBIDDEN_MESSAGE = "Allowlist writes only from the Archon server / local UI";

export function formatAllowlistError(error: unknown, fallback: string): string {
  if (error instanceof APIServiceError) {
    if (error.statusCode === 403) {
      return ALLOWLIST_WRITE_FORBIDDEN_MESSAGE;
    }
    return error.message || fallback;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}

export const allowlistService = {
  async getAllowlist(): Promise<AllowlistFile> {
    return callAPIWithETag<AllowlistFile>(ALLOWLIST_ENDPOINT);
  },

  async getDiscoveredPlugins(): Promise<string[]> {
    return callAPIWithETag<string[]>(DISCOVERED_ENDPOINT);
  },

  async mutateEntry(request: AllowlistEntryActionRequest): Promise<AllowlistFile> {
    return callAPIWithETag<AllowlistFile>(`${ALLOWLIST_ENDPOINT}/entries`, {
      method: "POST",
      body: JSON.stringify(request),
    });
  },

  async addEntry(section: AllowlistSection, entry: AllowlistEntry): Promise<AllowlistFile> {
    return this.mutateEntry({ action: "add", section, entry });
  },

  async removeEntry(section: AllowlistSection, name: string): Promise<AllowlistFile> {
    return this.mutateEntry({ action: "remove", section, name });
  },

  async setEntryEnabled(section: AllowlistSection, name: string, enabled: boolean): Promise<AllowlistFile> {
    return this.mutateEntry({
      action: enabled ? "enable" : "disable",
      section,
      name,
    });
  },
};

export function isValidSha256(value: string): boolean {
  return /^[a-fA-F0-9]{64}$/.test(value);
}

export function truncateHash(hash: string, visible = 8): string {
  if (hash.length <= visible * 2 + 3) {
    return hash;
  }
  return `${hash.slice(0, visible)}…${hash.slice(-visible)}`;
}
