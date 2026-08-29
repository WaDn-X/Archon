import { useState } from "react";
import { Key, ExternalLink, Save, Loader } from "lucide-react";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import { Select } from "../ui/Select";
import { useToast } from "../../features/shared/hooks/useToast";
import { credentialsService } from "../../services/credentialsService";

interface ProviderStepProps {
  onSaved: () => void;
  onSkip: () => void;
}

type OnboardingProvider = "openai" | "google" | "ollama" | "vertexai";

const VERTEX_DEFAULT_REGION = "us-central1";

export const ProviderStep = ({ onSaved, onSkip }: ProviderStepProps) => {
  const [provider, setProvider] = useState<OnboardingProvider>("openai");
  const [apiKey, setApiKey] = useState("");
  const [gcpProjectId, setGcpProjectId] = useState("");
  const [gcpRegion, setGcpRegion] = useState(VERTEX_DEFAULT_REGION);
  const [saving, setSaving] = useState(false);
  const { showToast } = useToast();

  const saveProviderSelection = async (selectedProvider: OnboardingProvider) => {
    await credentialsService.updateCredential({
      key: "LLM_PROVIDER",
      value: selectedProvider,
      is_encrypted: false,
      category: "rag_strategy",
    });
  };

  const handleSaveOpenAI = async () => {
    if (!apiKey.trim()) {
      showToast("Please enter an API key", "error");
      return;
    }

    setSaving(true);
    try {
      await credentialsService.createCredential({
        key: "OPENAI_API_KEY",
        value: apiKey,
        is_encrypted: true,
        category: "api_keys",
      });

      await saveProviderSelection("openai");

      showToast("API key saved successfully!", "success");
      localStorage.setItem("onboardingDismissed", "true");
      onSaved();
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      console.error("Failed to save API key:", error);

      if (
        errorMessage.includes("duplicate") ||
        errorMessage.includes("already exists")
      ) {
        showToast(
          "API key already exists. Please update it in Settings if you want to change it.",
          "warning",
        );
      } else if (
        errorMessage.includes("network") ||
        errorMessage.includes("fetch")
      ) {
        showToast(
          `Network error while saving API key: ${errorMessage}. Please check your connection.`,
          "error",
        );
      } else {
        showToast(`Failed to save API key: ${errorMessage}`, "error");
      }
    } finally {
      setSaving(false);
    }
  };

  const handleSaveVertexAI = async () => {
    const projectId = gcpProjectId.trim();
    if (!projectId) {
      showToast("Please enter your GCP project ID", "error");
      return;
    }

    setSaving(true);
    try {
      await credentialsService.updateCredential({
        key: "GCP_PROJECT_ID",
        value: projectId,
        is_encrypted: false,
        category: "rag_strategy",
      });

      await credentialsService.updateCredential({
        key: "GCP_REGION",
        value: gcpRegion.trim() || VERTEX_DEFAULT_REGION,
        is_encrypted: false,
        category: "rag_strategy",
      });

      await saveProviderSelection("vertexai");

      showToast("Vertex AI configuration saved!", "success");
      localStorage.setItem("onboardingDismissed", "true");
      onSaved();
    } catch (error) {
      console.error("Failed to save Vertex AI configuration:", error);
      showToast("Failed to save Vertex AI configuration", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleContinueOtherProvider = async () => {
    try {
      await saveProviderSelection(provider);
      const label =
        provider === "google"
          ? "Google Gemini"
          : provider === "ollama"
            ? "Ollama"
            : provider;
      showToast(`${label} selected as provider`, "success");
      localStorage.setItem("onboardingDismissed", "true");
      onSaved();
    } catch (error) {
      console.error("Failed to save provider selection:", error);
      showToast("Failed to save provider selection", "error");
    }
  };

  const handleSkip = () => {
    showToast("You can configure your provider in Settings", "info");
    localStorage.setItem("onboardingDismissed", "true");
    onSkip();
  };

  return (
    <div className="space-y-6">
      <div>
        <Select
          label="Select AI Provider"
          value={provider}
          onChange={(e) => setProvider(e.target.value as OnboardingProvider)}
          options={[
            { value: "openai", label: "OpenAI" },
            { value: "google", label: "Google Gemini" },
            { value: "vertexai", label: "Vertex AI (GCP)" },
            { value: "ollama", label: "Ollama (Local)" },
          ]}
          accentColor="green"
        />
        <p className="mt-2 text-sm text-gray-600 dark:text-zinc-400">
          {provider === "openai" &&
            "OpenAI provides powerful models like GPT-4. You'll need an API key from OpenAI."}
          {provider === "google" &&
            "Google Gemini offers advanced AI capabilities. Configure in Settings after setup."}
          {provider === "vertexai" &&
            "Vertex AI uses your Google Cloud project with Application Default Credentials (ADC). No API key required."}
          {provider === "ollama" &&
            "Ollama runs models locally on your machine. Configure in Settings after setup."}
        </p>
        {provider === "vertexai" && (
          <p className="mt-1 text-xs text-gray-500 dark:text-zinc-500">
            Vertex AI nutzt ADC — z. B.{" "}
            <code className="text-[#011379] dark:text-[#D4AF37]">gcloud auth application-default login</code>
          </p>
        )}
      </div>

      {provider === "openai" && (
        <>
          <div>
            <Input
              label="OpenAI API Key"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              accentColor="green"
              icon={<Key className="w-4 h-4" />}
            />
            <p className="mt-2 text-sm text-gray-600 dark:text-zinc-400">
              Your API key will be encrypted and stored securely.
            </p>
          </div>

          <div className="flex items-center gap-2 text-sm">
            <a
              href="https://platform.openai.com/api-keys"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 flex items-center gap-1"
            >
              Get an API key from OpenAI
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              variant="primary"
              size="lg"
              onClick={handleSaveOpenAI}
              disabled={saving || !apiKey.trim()}
              icon={
                saving ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )
              }
              className="flex-1"
            >
              {saving ? "Saving..." : "Save & Continue"}
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={handleSkip}
              disabled={saving}
              className="flex-1"
            >
              Skip for Now
            </Button>
          </div>
        </>
      )}

      {provider === "vertexai" && (
        <>
          <div className="space-y-4 p-4 rounded-lg border border-[#011379]/30 bg-[#011379]/5">
            <Input
              label="GCP Project ID"
              value={gcpProjectId}
              onChange={(e) => setGcpProjectId(e.target.value)}
              placeholder="my-gcp-project"
              accentColor="green"
            />
            <Input
              label="GCP Region (optional)"
              value={gcpRegion}
              onChange={(e) => setGcpRegion(e.target.value)}
              placeholder={VERTEX_DEFAULT_REGION}
              accentColor="green"
            />
            <p className="text-sm text-gray-600 dark:text-zinc-400">
              Authentication uses Application Default Credentials on the Archon server
              (service account key file or <code>gcloud auth application-default login</code>).
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              variant="primary"
              size="lg"
              onClick={handleSaveVertexAI}
              disabled={saving || !gcpProjectId.trim()}
              icon={
                saving ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )
              }
              className="flex-1"
            >
              {saving ? "Saving..." : "Save & Continue"}
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={handleSkip}
              disabled={saving}
              className="flex-1"
            >
              Skip for Now
            </Button>
          </div>
        </>
      )}

      {provider !== "openai" && provider !== "vertexai" && (
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              {provider === "google" &&
                "Google Gemini configuration will be available in Settings after setup."}
              {provider === "ollama" &&
                "Ollama configuration will be available in Settings after setup. Make sure Ollama is running locally."}
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              variant="primary"
              size="lg"
              onClick={handleContinueOtherProvider}
              className="flex-1"
            >
              Continue with {provider === "google" ? "Gemini" : "Ollama"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
