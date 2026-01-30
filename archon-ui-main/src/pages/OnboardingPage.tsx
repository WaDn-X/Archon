import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, Key, Database, FolderOpen, Check, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { ProviderStep } from '../components/onboarding/ProviderStep';
import { KnowledgeBaseStep } from '../components/onboarding/KnowledgeBaseStep';
import { ProjectStep } from '../components/onboarding/ProjectStep';
import { FeaturesTourStep } from '../components/onboarding/FeaturesTourStep';

export const OnboardingPage = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const navigate = useNavigate();

  // Step handlers
  const handleWelcomeComplete = () => setCurrentStep(2);
  const handleProviderComplete = () => setCurrentStep(3);
  const handleKnowledgeBaseComplete = () => setCurrentStep(4);
  const handleProjectComplete = () => setCurrentStep(5);
  const handleFeaturesComplete = () => setCurrentStep(6);

  const handleProviderSkip = () => {
    // Navigate to settings with guidance
    navigate('/settings');
  };

  const handleKnowledgeBaseSkip = () => setCurrentStep(4);
  const handleProjectSkip = () => setCurrentStep(5);

  const handleComplete = () => {
    // Mark onboarding as dismissed and navigate to home
    localStorage.setItem('onboardingDismissed', 'true');
    navigate('/');
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5 }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <motion.div
        initial="hidden"
        animate="visible"
        variants={containerVariants}
        className="w-full max-w-2xl"
      >
        {/* Progress Indicators */}
        <motion.div variants={itemVariants} className="flex justify-center mb-8 gap-2">
          {[1, 2, 3, 4, 5, 6].map((step) => (
            <div
              key={step}
              className={`h-2 w-12 rounded-full transition-colors duration-300 ${
                step <= currentStep
                  ? 'bg-blue-500'
                  : 'bg-gray-200 dark:bg-zinc-800'
              }`}
            />
          ))}
        </motion.div>

        {/* Step 1: Welcome */}
        {currentStep === 1 && (
          <motion.div variants={itemVariants}>
            <Card className="p-12 text-center">
              <div className="flex justify-center mb-6">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                  <Sparkles className="w-10 h-10 text-white" />
                </div>
              </div>
              
              <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-4">
                Welcome to Archon
              </h1>
              
              <p className="text-lg text-gray-600 dark:text-zinc-400 mb-8 max-w-md mx-auto">
                Let's get you set up with your AI provider in just a few steps. This will enable intelligent knowledge retrieval and code assistance.
              </p>
              
              <Button
                variant="primary"
                size="lg"
                icon={<ArrowRight className="w-5 h-5 ml-2" />}
                iconPosition="right"
                onClick={handleWelcomeComplete}
                className="min-w-[200px]"
              >
                Get Started
              </Button>
            </Card>
          </motion.div>
        )}

        {/* Step 2: Provider Setup */}
        {currentStep === 2 && (
          <motion.div variants={itemVariants}>
            <Card className="p-12">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-green-500 to-teal-600 flex items-center justify-center mr-4">
                  <Key className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white">
                  Configure AI Provider
                </h2>
              </div>

              <ProviderStep
                onSaved={handleProviderComplete}
                onSkip={handleProviderSkip}
              />
            </Card>
          </motion.div>
        )}

        {/* Step 3: Knowledge Base Setup */}
        {currentStep === 3 && (
          <motion.div variants={itemVariants}>
            <Card className="p-12">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center mr-4">
                  <Database className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white">
                  Build Your Knowledge Base
                </h2>
              </div>

              <KnowledgeBaseStep
                onComplete={handleKnowledgeBaseComplete}
                onSkip={handleKnowledgeBaseSkip}
              />
            </Card>
          </motion.div>
        )}

        {/* Step 4: Project Creation */}
        {currentStep === 4 && (
          <motion.div variants={itemVariants}>
            <Card className="p-12">
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center mr-4">
                  <FolderOpen className="w-6 h-6 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-800 dark:text-white">
                  Create Your First Project
                </h2>
              </div>

              <ProjectStep
                onComplete={handleProjectComplete}
                onSkip={handleProjectSkip}
              />
            </Card>
          </motion.div>
        )}

        {/* Step 5: Features Tour */}
        {currentStep === 5 && (
          <motion.div variants={itemVariants}>
            <Card className="p-12">
              <FeaturesTourStep
                onComplete={handleFeaturesComplete}
              />
            </Card>
          </motion.div>
        )}

        {/* Step 6: All Set */}
        {currentStep === 6 && (
          <motion.div variants={itemVariants}>
            <Card className="p-12 text-center">
              <div className="flex justify-center mb-6">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{
                    type: "spring",
                    stiffness: 260,
                    damping: 20
                  }}
                  className="w-20 h-20 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center"
                >
                  <Check className="w-10 h-10 text-white" />
                </motion.div>
              </div>

              <h1 className="text-3xl font-bold text-gray-800 dark:text-white mb-4">
                Welcome to Zippy Archon!
              </h1>

              <p className="text-lg text-gray-600 dark:text-zinc-400 mb-8 max-w-md mx-auto">
                You're all set to start building amazing things. Explore the features, create your first project, and let AI-powered workflows accelerate your development.
              </p>

              <div className="space-y-4">
                <Button
                  variant="primary"
                  size="lg"
                  onClick={handleComplete}
                  className="min-w-[200px]"
                >
                  Start Building
                </Button>

                <div className="text-sm text-gray-500 dark:text-zinc-500 space-y-1">
                  <p>💡 <strong>Pro Tips:</strong></p>
                  <p>• Visit the Knowledge Base to add your first data sources</p>
                  <p>• Create a project to start organizing your tasks</p>
                  <p>• Check Settings to customize your AI provider preferences</p>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
};