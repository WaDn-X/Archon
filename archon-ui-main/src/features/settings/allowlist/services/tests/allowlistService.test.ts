import { describe, expect, it } from "vitest";
import { APIServiceError } from "@/features/shared/types/errors";
import {
  ALLOWLIST_WRITE_FORBIDDEN_MESSAGE,
  formatAllowlistError,
  isValidSha256,
  truncateHash,
} from "../allowlistService";

describe("allowlistService helpers", () => {
  it("validates sha256 hex digests", () => {
    const valid = "a".repeat(64);
    expect(isValidSha256(valid)).toBe(true);
    expect(isValidSha256("short")).toBe(false);
    expect(isValidSha256(`${valid}extra`)).toBe(false);
  });

  it("truncates long hashes for display", () => {
    const hash = "abcdef12".repeat(8);
    expect(truncateHash(hash)).toBe("abcdef12…abcdef12");
  });

  it("maps 403 errors to the local UI write restriction message", () => {
    const error = new APIServiceError("Allowlist writes are restricted", "HTTP_ERROR", 403);
    expect(formatAllowlistError(error, "fallback")).toBe(ALLOWLIST_WRITE_FORBIDDEN_MESSAGE);
  });
});
