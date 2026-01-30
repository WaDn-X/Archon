import { useState } from "react";
import { Database, FileText, Globe, ArrowRight, Check } from "lucide-react";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

interface KnowledgeBaseStepProps {
  onComplete: () => void;
  onSkip: () => void;
}

export const KnowledgeBaseStep = ({ onComplete, onSkip }: KnowledgeBaseStepProps) => {
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);

  const knowledgeOptions = [
    {
      id: "website",
      title: "Website Crawling",
      description: "Add knowledge from websites, documentation, or blogs",
      icon: Globe,
      recommended: true,
    },
    {
      id: "documents",
      title: "Document Upload",
      description: "Upload PDFs, text files, or other documents",
      icon: FileText,
      recommended: true,
    },
    {
      id: "skip",
      title: "Skip for Now",
      description: "You can add knowledge sources later in the Knowledge Base",
      icon: ArrowRight,
      recommended: false,
    },
  ];

  const handleOptionSelect = (optionId: string) => {
    if (optionId === "skip") {
      setSelectedOptions([optionId]);
    } else {
      setSelectedOptions(prev =>
        prev.includes(optionId)
          ? prev.filter(id => id !== optionId)
          : [...prev.filter(id => id !== "skip"), optionId]
      );
    }
  };

  const handleContinue = () => {
    if (selectedOptions.includes("skip")) {
      onSkip();
    } else {
      onComplete();
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-2">
          Set Up Your Knowledge Base
        </h3>
        <p className="text-gray-600 dark:text-zinc-400">
          Add knowledge sources to power your AI assistant with relevant information
        </p>
      </div>

      <div className="grid gap-4">
        {knowledgeOptions.map((option) => {
          const Icon = option.icon;
          const isSelected = selectedOptions.includes(option.id);

          return (
            <Card
              key={option.id}
              className={`p-4 cursor-pointer transition-all duration-200 ${
                isSelected
                  ? "ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900/20"
                  : "hover:shadow-md"
              }`}
              onClick={() => handleOptionSelect(option.id)}
            >
              <div className="flex items-start gap-4">
                <div className={`p-2 rounded-lg ${
                  isSelected
                    ? "bg-blue-500 text-white"
                    : "bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-zinc-400"
                }`}>
                  <Icon className="w-5 h-5" />
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium text-gray-800 dark:text-white">
                      {option.title}
                    </h4>
                    {option.recommended && (
                      <span className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full">
                        Recommended
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-zinc-400">
                    {option.description}
                  </p>
                </div>

                {isSelected && (
                  <div className="text-blue-500">
                    <Check className="w-5 h-5" />
                  </div>
                )}
              </div>
            </Card>
          );
        })}
      </div>

      <div className="flex gap-3 pt-4">
        <Button
          variant="primary"
          size="lg"
          onClick={handleContinue}
          disabled={selectedOptions.length === 0}
          className="flex-1"
        >
          {selectedOptions.includes("skip") ? "Skip for Now" : "Continue"}
        </Button>
      </div>

      <div className="text-center">
        <p className="text-sm text-gray-500 dark:text-zinc-500">
          You can always add or modify knowledge sources later
        </p>
      </div>
    </div>
  );
};


