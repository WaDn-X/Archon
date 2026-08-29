/**
 * Execute allowlist types (plugins and sandbox executors)
 */

export interface AllowlistEntry {
  name: string;
  sha256: string;
  enabled: boolean;
}

export interface AllowlistFile {
  plugins: AllowlistEntry[];
  executors: AllowlistEntry[];
}

export type AllowlistSection = "plugins" | "executors";

export type AllowlistEntryAction = "add" | "remove" | "enable" | "disable";

export interface AllowlistEntryActionRequest {
  action: AllowlistEntryAction;
  section: AllowlistSection;
  entry?: AllowlistEntry;
  name?: string;
}

export const FIRST_PARTY_EXECUTORS = ["claude", "git", "gh"] as const;

export type FirstPartyExecutor = (typeof FIRST_PARTY_EXECUTORS)[number];
