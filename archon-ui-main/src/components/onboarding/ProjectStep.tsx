import { useState } from "react";
import { FolderOpen, GitBranch, Check, ArrowRight } from "lucide-react";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

interface ProjectStepProps {
  onComplete: () => void;
  onSkip: () => void;
}

export const ProjectStep = ({ onComplete, onSkip }: ProjectStepProps) => {
  const [selectedOption, setSelectedOption] = useState<string>("");

  const projectOptions = [
    {
      id: "create",
      title: "Create Your First Project",
      description: "Start a new project to organize your tasks and track progress",
      icon: FolderOpen,
      action: "Get Started",
    },
    {
      id: "import",
      title: "Import from Repository",
      description: "Connect an existing Git repository to get started quickly",
      icon: GitBranch,
      action: "Import Repository",
    },
    {
      id: "explore",
      title: "Explore Features First",
      description: "Take a quick tour of the features before creating your project",
      icon: ArrowRight,
      action: "Explore Features",
    },
  ];

  const handleContinue = () => {
    if (selectedOption === "explore") {
      onSkip();
    } else {
      onComplete();
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-2">
          Create Your First Project
        </h3>
        <p className="text-gray-600 dark:text-zinc-400">
          Projects help you organize tasks, track progress, and collaborate with your team
        </p>
      </div>

      <div className="grid gap-4">
        {projectOptions.map((option) => {
          const Icon = option.icon;
          const isSelected = selectedOption === option.id;

          return (
            <Card
              key={option.id}
              className={`p-4 cursor-pointer transition-all duration-200 ${
                isSelected
                  ? "ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-900/20"
                  : "hover:shadow-md"
              }`}
              onClick={() => setSelectedOption(option.id)}
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
                  <h4 className="font-medium text-gray-800 dark:text-white mb-1">
                    {option.title}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-zinc-400 mb-3">
                    {option.description}
                  </p>
                  <Button
                    variant={isSelected ? "primary" : "outline"}
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedOption(option.id);
                    }}
                  >
                    {option.action}
                  </Button>
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
          disabled={!selectedOption}
          className="flex-1"
        >
          {selectedOption === "explore" ? "Take the Tour" : "Continue"}
        </Button>
      </div>

      <div className="text-center">
        <p className="text-sm text-gray-500 dark:text-zinc-500">
          Don't worry, you can create multiple projects and switch between them anytime
        </p>
      </div>
    </div>
  );
};


