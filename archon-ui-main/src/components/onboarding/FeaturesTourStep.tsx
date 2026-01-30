import { useState } from "react";
import { Bot, Database, CheckSquare, Users, Zap, ArrowRight } from "lucide-react";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

interface FeaturesTourStepProps {
  onComplete: () => void;
}

export const FeaturesTourStep = ({ onComplete }: FeaturesTourStepProps) => {
  const [currentFeature, setCurrentFeature] = useState(0);

  const features = [
    {
      icon: Bot,
      title: "AI-Powered Assistance",
      description: "Get intelligent help with coding, task planning, and problem solving using advanced AI models.",
      benefits: ["Code generation and review", "Task breakdown and planning", "Intelligent suggestions"],
    },
    {
      icon: Database,
      title: "Knowledge Base",
      description: "Build and maintain a personal knowledge base with website crawling and document uploads.",
      benefits: ["Website content extraction", "Document processing", "Semantic search"],
    },
    {
      icon: CheckSquare,
      title: "Project Management",
      description: "Organize tasks, track progress, and collaborate with your team using intelligent workflows.",
      benefits: ["Task organization", "Progress tracking", "Team collaboration"],
    },
    {
      icon: Users,
      title: "Team Collaboration",
      description: "Work together in real-time with live updates, comments, and shared knowledge.",
      benefits: ["Real-time collaboration", "Live task updates", "Shared workspaces"],
    },
    {
      icon: Zap,
      title: "Workflow Automation",
      description: "Automate repetitive tasks and workflows with intelligent agents and integrations.",
      benefits: ["Automated task creation", "Git integration", "API integrations"],
    },
  ];

  const nextFeature = () => {
    if (currentFeature < features.length - 1) {
      setCurrentFeature(currentFeature + 1);
    } else {
      onComplete();
    }
  };

  const skipTour = () => {
    onComplete();
  };

  const currentFeatureData = features[currentFeature];
  const Icon = currentFeatureData.icon;

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-2">
          Discover Archon Features
        </h3>
        <p className="text-gray-600 dark:text-zinc-400">
          Here's what you can do with Archon
        </p>
      </div>

      {/* Progress indicators */}
      <div className="flex justify-center gap-2 mb-6">
        {features.map((_, index) => (
          <div
            key={index}
            className={`h-2 w-8 rounded-full transition-colors duration-300 ${
              index <= currentFeature
                ? "bg-blue-500"
                : "bg-gray-200 dark:bg-zinc-800"
            }`}
          />
        ))}
      </div>

      {/* Feature card */}
      <Card className="p-6">
        <div className="text-center mb-6">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mx-auto mb-4">
            <Icon className="w-8 h-8 text-white" />
          </div>
          <h4 className="text-xl font-semibold text-gray-800 dark:text-white mb-2">
            {currentFeatureData.title}
          </h4>
          <p className="text-gray-600 dark:text-zinc-400 mb-4">
            {currentFeatureData.description}
          </p>
        </div>

        {/* Benefits */}
        <div className="space-y-2 mb-6">
          {currentFeatureData.benefits.map((benefit, index) => (
            <div key={index} className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
              <span className="text-sm text-gray-600 dark:text-zinc-400">
                {benefit}
              </span>
            </div>
          ))}
        </div>

        {/* Navigation */}
        <div className="flex gap-3">
          <Button
            variant="outline"
            size="lg"
            onClick={skipTour}
            className="flex-1"
          >
            Skip Tour
          </Button>
          <Button
            variant="primary"
            size="lg"
            onClick={nextFeature}
            icon={<ArrowRight className="w-4 h-4 ml-2" />}
            iconPosition="right"
            className="flex-1"
          >
            {currentFeature === features.length - 1 ? "Get Started" : "Next"}
          </Button>
        </div>
      </Card>

      {/* Feature navigation dots */}
      <div className="flex justify-center gap-2">
        {features.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentFeature(index)}
            className={`w-3 h-3 rounded-full transition-colors duration-300 ${
              index === currentFeature
                ? "bg-blue-500"
                : "bg-gray-300 dark:bg-zinc-600 hover:bg-gray-400 dark:hover:bg-zinc-500"
            }`}
          />
        ))}
      </div>
    </div>
  );
};






