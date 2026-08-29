import { Copy, Loader2, Plus, RefreshCw, Shield, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { useToast } from "@/features/shared/hooks/useToast";
import { copyToClipboard } from "@/features/shared/utils/clipboard";
import { Button } from "@/features/ui/primitives/button";
import { Input } from "@/features/ui/primitives/input";
import { Label } from "@/features/ui/primitives/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/features/ui/primitives/select";
import { Switch } from "@/features/ui/primitives/switch";
import { useAllowlist, useAllowlistMutations, useDiscoveredPlugins } from "../hooks/useAllowlistQueries";
import { useAllowlistMessages } from "../i18n/useAllowlistMessages";
import { formatAllowlistError, isValidSha256, truncateHash } from "../services/allowlistService";
import type { AllowlistEntry, AllowlistSection } from "../types";
import { FIRST_PARTY_EXECUTORS } from "../types";

interface AddEntryFormProps {
  section: AllowlistSection;
  onCancel: () => void;
}

function AddEntryForm({ section, onCancel }: AddEntryFormProps) {
  const { t } = useAllowlistMessages();
  const { showToast } = useToast();
  const { addEntry } = useAllowlistMutations();
  const { data: discovered = [] } = useDiscoveredPlugins();
  const [name, setName] = useState("");
  const [sha256, setSha256] = useState("");

  const handleDiscoveredSelect = (value: string) => {
    if (!value) {
      return;
    }
    setName(value);
  };

  const handleSubmit = async () => {
    const trimmedName = name.trim();
    const trimmedHash = sha256.trim().toLowerCase();

    if (!trimmedName) {
      showToast(t("nameRequired"), "error");
      return;
    }

    if (!isValidSha256(trimmedHash)) {
      showToast(t("invalidHash"), "error");
      return;
    }

    try {
      await addEntry.mutateAsync({
        section,
        entry: { name: trimmedName, sha256: trimmedHash, enabled: false },
      });
      showToast(t("addSuccess"), "success");
      onCancel();
    } catch (error) {
      showToast(formatAllowlistError(error, t("loadError")), "error");
    }
  };

  return (
    <div className="rounded-lg border border-[#011379]/30 bg-[#011379]/5 p-4 space-y-4">
      {section === "plugins" && discovered.length > 0 && (
        <div className="space-y-2">
          <Label className="text-gray-300 text-sm">{t("discoveredPlugins")}</Label>
          <Select onValueChange={handleDiscoveredSelect}>
            <SelectTrigger color="cyan" className="w-full">
              <SelectValue placeholder={t("selectPlugin")} />
            </SelectTrigger>
            <SelectContent color="cyan">
              {discovered.map((pluginName) => (
                <SelectItem key={pluginName} value={pluginName} color="cyan">
                  {pluginName}.py
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor={`${section}-name`} className="text-gray-300 text-sm">
            {t("nameLabel")}
          </Label>
          <Input
            id={`${section}-name`}
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder={t("namePlaceholder")}
            className="font-mono"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${section}-hash`} className="text-gray-300 text-sm">
            {t("hashLabel")}
          </Label>
          <Input
            id={`${section}-hash`}
            value={sha256}
            onChange={(event) => setSha256(event.target.value)}
            placeholder={t("hashPlaceholder")}
            className="font-mono"
          />
        </div>
      </div>

      <p className="text-xs text-gray-400">{t("hashHelper")}</p>

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          onClick={handleSubmit}
          disabled={addEntry.isPending}
          className="bg-[#017913]/20 border-[#017913]/50 hover:bg-[#017913]/30"
        >
          {addEntry.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          <span>{t("addEntry")}</span>
        </Button>
        <Button type="button" variant="ghost" onClick={onCancel}>
          {t("cancel")}
        </Button>
      </div>
    </div>
  );
}

interface EntryRowProps {
  entry: AllowlistEntry;
  section: AllowlistSection;
}

function EntryRow({ entry, section }: EntryRowProps) {
  const { t } = useAllowlistMessages();
  const { showToast } = useToast();
  const { removeEntry, setEntryEnabled } = useAllowlistMutations();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const result = await copyToClipboard(entry.sha256);
    if (result.success) {
      setCopied(true);
      showToast(t("copied"), "success");
      window.setTimeout(() => setCopied(false), 1500);
    }
  };

  const handleToggle = async (enabled: boolean) => {
    try {
      await setEntryEnabled.mutateAsync({ section, name: entry.name, enabled });
      showToast(t("toggleSuccess"), "success");
    } catch (error) {
      showToast(formatAllowlistError(error, t("loadError")), "error");
    }
  };

  const handleRemove = async () => {
    try {
      await removeEntry.mutateAsync({ section, name: entry.name });
      showToast(t("removeSuccess"), "success");
    } catch (error) {
      showToast(formatAllowlistError(error, t("loadError")), "error");
    }
  };

  const isBusy = removeEntry.isPending || setEntryEnabled.isPending;

  return (
    <tr className="border-t border-gray-700/60">
      <td className="py-3 pr-3 font-mono text-sm text-white">{entry.name}</td>
      <td className="py-3 pr-3">
        <div className="flex items-center gap-2">
          <code className="text-xs text-gray-300 font-mono" title={entry.sha256}>
            {truncateHash(entry.sha256)}
          </code>
          <button
            type="button"
            onClick={handleCopy}
            className="p-1 rounded hover:bg-gray-700/50 text-gray-400 hover:text-[#D4AF37] transition-colors"
            aria-label={t("copyHash")}
            title={copied ? t("copied") : t("copyHash")}
          >
            <Copy className="w-3.5 h-3.5" />
          </button>
        </div>
      </td>
      <td className="py-3 pr-3">
        <Switch
          checked={entry.enabled}
          onCheckedChange={handleToggle}
          disabled={isBusy}
          color="green"
          size="sm"
          aria-label={entry.enabled ? t("enabled") : t("disabled")}
        />
      </td>
      <td className="py-3 text-right">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={handleRemove}
          disabled={isBusy}
          className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
        >
          <Trash2 className="w-4 h-4" />
          <span className="sr-only">{t("remove")}</span>
        </Button>
      </td>
    </tr>
  );
}

interface EntryTableProps {
  section: AllowlistSection;
  entries: AllowlistEntry[];
  emptyLabel: string;
  addLabel: string;
}

function EntryTable({ section, entries, emptyLabel, addLabel }: EntryTableProps) {
  const { t } = useAllowlistMessages();
  const [showAddForm, setShowAddForm] = useState(false);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h4 className="text-sm font-semibold text-white">
          {section === "plugins" ? t("pluginsHeading") : t("executorsHeading")}
        </h4>
        {!showAddForm && (
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => setShowAddForm(true)}
            className="border-[#011379]/40"
          >
            <Plus className="w-4 h-4" />
            <span>{addLabel}</span>
          </Button>
        )}
      </div>

      {showAddForm && <AddEntryForm section={section} onCancel={() => setShowAddForm(false)} />}

      {entries.length === 0 ? (
        <p className="text-sm text-gray-400">{emptyLabel}</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-700/60">
          <table className="min-w-full text-left">
            <thead className="bg-gray-900/40">
              <tr>
                <th className="px-3 py-2 text-xs font-medium text-gray-400">{t("columnName")}</th>
                <th className="px-3 py-2 text-xs font-medium text-gray-400">{t("columnHash")}</th>
                <th className="px-3 py-2 text-xs font-medium text-gray-400">{t("columnEnabled")}</th>
                <th className="px-3 py-2 text-xs font-medium text-gray-400 text-right">{t("columnActions")}</th>
              </tr>
            </thead>
            <tbody className="px-3">
              {entries.map((entry) => (
                <EntryRow key={`${section}-${entry.name}`} entry={entry} section={section} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function ExecuteAllowlistSettings() {
  const { t } = useAllowlistMessages();
  const { data, isLoading, error, refetch, isFetching } = useAllowlist();

  const builtinExecutors = useMemo(() => FIRST_PARTY_EXECUTORS, []);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-gray-400 text-sm py-4">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>{t("loading")}</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-red-400">{t("loadError")}</p>
        <Button type="button" size="sm" variant="outline" onClick={() => refetch()}>
          <RefreshCw className="w-4 h-4" />
          <span>Retry</span>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-sm text-gray-400">{t("description")}</p>
          <p className="text-xs text-gray-500">{t("builtinMcpHint")}</p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors disabled:opacity-50"
          aria-label="Refresh allowlist"
        >
          <RefreshCw className={`w-4 h-4 text-gray-400 ${isFetching ? "animate-spin" : ""}`} />
        </button>
      </div>

      <EntryTable section="plugins" entries={data.plugins} emptyLabel={t("emptyPlugins")} addLabel={t("addPlugin")} />

      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-[#D4AF37]" />
          <h4 className="text-sm font-semibold text-white">{t("builtinExecutorsHeading")}</h4>
        </div>
        <p className="text-xs text-gray-500">{t("builtinExecutorsHint")}</p>
        <div className="flex flex-wrap gap-2">
          {builtinExecutors.map((executor) => (
            <span
              key={executor}
              className="inline-flex items-center gap-1 rounded-full border border-[#017913]/40 bg-[#017913]/10 px-3 py-1 text-xs font-mono text-[#017913]"
            >
              {executor}
              <span className="text-[10px] uppercase tracking-wide text-gray-400">{t("builtinBadge")}</span>
            </span>
          ))}
        </div>
      </div>

      <EntryTable
        section="executors"
        entries={data.executors}
        emptyLabel={t("emptyExecutors")}
        addLabel={t("addExecutor")}
      />
    </div>
  );
}
