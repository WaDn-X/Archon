import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertCircle, Bug, RefreshCw, Wifi, WifiOff, Server, Database, AlertTriangle, Clock, Lock } from "lucide-react";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { BugReportModal } from "./BugReportModal";
import { bugReportService, BugContext } from "../../services/bugReportService";

interface Props {
  children: ReactNode;
  fallback?: (error: Error, errorInfo: ErrorInfo) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  showBugReport: boolean;
  bugContext: BugContext | null;
}

export class ErrorBoundaryWithBugReport extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showBugReport: false,
      bugContext: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // Collect bug context automatically when error occurs
    this.collectBugContext(error);
  }

  private async collectBugContext(error: Error) {
    try {
      const context = await bugReportService.collectBugContext(error);
      this.setState({ bugContext: context });
    } catch (contextError) {
      console.error("Failed to collect bug context:", contextError);
    }
  }

  private handleReportBug = () => {
    this.setState({ showBugReport: true });
  };

  private handleCloseBugReport = () => {
    this.setState({ showBugReport: false });
  };

  private getErrorCategory = (error: Error): { type: string; icon: any; title: string; suggestion: string; severity: 'low' | 'medium' | 'high' } => {
    const message = error.message.toLowerCase();
    const name = error.name.toLowerCase();

    // Network/Connection errors
    if (message.includes('network') || message.includes('fetch') || message.includes('connection') ||
        message.includes('offline') || message.includes('no internet')) {
      return {
        type: 'network',
        icon: WifiOff,
        title: 'Connection Problem',
        suggestion: 'Check your internet connection and try again. If the problem persists, the server might be temporarily unavailable.',
        severity: 'medium'
      };
    }

    // Server/API errors
    if (message.includes('server') || message.includes('api') ||
        message.includes('500') || message.includes('502') || message.includes('503') ||
        message.includes('internal server error') || message.includes('bad gateway')) {
      return {
        type: 'server',
        icon: Server,
        title: 'Server Error',
        suggestion: 'The server is temporarily unavailable. Please try again in a few moments. If this continues, please report the issue.',
        severity: 'high'
      };
    }

    // Database errors
    if (message.includes('database') || message.includes('supabase') || message.includes('sql') ||
        message.includes('connection refused') || message.includes('timeout')) {
      return {
        type: 'database',
        icon: Database,
        title: 'Database Error',
        suggestion: 'There was an issue with the database. Please refresh the page. If the problem persists, the database might be temporarily unavailable.',
        severity: 'high'
      };
    }

    // Authentication errors
    if (message.includes('unauthorized') || message.includes('forbidden') ||
        message.includes('401') || message.includes('403') || message.includes('auth')) {
      return {
        type: 'auth',
        icon: Lock,
        title: 'Authentication Required',
        suggestion: 'Please log in or check your permissions. Your session might have expired.',
        severity: 'medium'
      };
    }

    // Rate limiting errors
    if (message.includes('rate limit') || message.includes('too many requests') ||
        message.includes('429')) {
      return {
        type: 'rate_limit',
        icon: AlertTriangle,
        title: 'Too Many Requests',
        suggestion: 'You\'re making requests too quickly. Please wait a moment before trying again.',
        severity: 'low'
      };
    }

    // Validation errors
    if (message.includes('validation') || message.includes('invalid') ||
        message.includes('400') || message.includes('bad request')) {
      return {
        type: 'validation',
        icon: CheckSquare,
        title: 'Invalid Input',
        suggestion: 'Please check your input and try again. Make sure all required fields are filled correctly.',
        severity: 'low'
      };
    }

    // Default error
    return {
      type: 'general',
      icon: AlertTriangle,
      title: 'Something went wrong',
      suggestion: 'An unexpected error occurred. Please try refreshing the page or report this issue if it persists.',
      severity: 'medium'
    };
  };

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showBugReport: false,
      bugContext: null,
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleAutoRetry = async () => {
    const errorCategory = this.getErrorCategory(this.state.error!);

    // Auto-retry for retryable errors
    if (errorCategory.type === 'network' || errorCategory.type === 'timeout') {
      // Wait 3 seconds and then retry
      setTimeout(() => {
        this.setState({
          hasError: false,
          error: null,
          errorInfo: null,
          showBugReport: false,
          bugContext: null,
        });
      }, 3000); // 3 second delay
    }
  };

  private getRetryDelay = (errorType: string): number => {
    switch (errorType) {
      case 'network':
      case 'timeout':
        return 2000; // 2 seconds
      case 'server':
        return 5000; // 5 seconds
      default:
        return 0;
    }
  };

  render() {
    if (this.state.hasError && this.state.error) {
      // Custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.state.errorInfo!);
      }

      // Get error category and styling
      const errorCategory = this.getErrorCategory(this.state.error);
      const ErrorIcon = errorCategory.icon;

      // Color scheme based on error type and severity
      const getErrorColors = (type: string, severity: 'low' | 'medium' | 'high') => {
        const baseColors = {
          network: { bg: 'bg-orange-100 dark:bg-orange-900/20', text: 'text-orange-600 dark:text-orange-400', border: 'border-orange-200 dark:border-orange-800' },
          server: { bg: 'bg-red-100 dark:bg-red-900/20', text: 'text-red-600 dark:text-red-400', border: 'border-red-200 dark:border-red-800' },
          database: { bg: 'bg-purple-100 dark:bg-purple-900/20', text: 'text-purple-600 dark:text-purple-400', border: 'border-purple-200 dark:border-purple-800' },
          auth: { bg: 'bg-blue-100 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400', border: 'border-blue-200 dark:border-blue-800' },
          rate_limit: { bg: 'bg-yellow-100 dark:bg-yellow-900/20', text: 'text-yellow-600 dark:text-yellow-400', border: 'border-yellow-200 dark:border-yellow-800' },
          validation: { bg: 'bg-green-100 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400', border: 'border-green-200 dark:border-green-800' },
          timeout: { bg: 'bg-yellow-100 dark:bg-yellow-900/20', text: 'text-yellow-600 dark:text-yellow-400', border: 'border-yellow-200 dark:border-yellow-800' },
          general: { bg: 'bg-gray-100 dark:bg-gray-900/20', text: 'text-gray-600 dark:text-gray-400', border: 'border-gray-200 dark:border-gray-800' }
        };

        const colors = baseColors[type] || baseColors.general;

        // Adjust intensity based on severity
        if (severity === 'high') {
          colors.bg = colors.bg.replace('100', '200').replace('900/20', '800/30');
          colors.text = colors.text.replace('600', '700').replace('400', '300');
        }

        return colors;
      };

      const colors = getErrorColors(errorCategory.type, errorCategory.severity);

      // Default error UI
      return (
        <>
          <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
            <Card className={`max-w-lg w-full border-2 ${colors.border}`}>
              <div className="p-6 text-center">
                {/* Error Icon */}
                <div className={`w-16 h-16 mx-auto mb-4 ${colors.bg} rounded-full flex items-center justify-center`}>
                  <ErrorIcon className={`w-8 h-8 ${colors.text}`} />
                </div>

                {/* Error Title */}
                <h1 className="text-xl font-bold text-gray-800 dark:text-white mb-2">
                  {errorCategory.title}
                </h1>

                {/* User-friendly Error Message */}
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {errorCategory.suggestion}
                </p>

                {/* Technical Details (collapsible) */}
                <details className="text-left mb-6">
                  <summary className="cursor-pointer text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-sm mb-2">
                    Technical details
                  </summary>
                  <div className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono overflow-auto max-h-32">
                    <div className="mb-2">
                      <strong>Error:</strong> {this.state.error.name}
                    </div>
                    <div className="mb-2">
                      <strong>Message:</strong> {this.state.error.message}
                    </div>
                    {this.state.error.stack && (
                      <div>
                        <strong>Stack:</strong>
                        <pre className="mt-1 whitespace-pre-wrap">
                          {this.state.error.stack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>


                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  {/* Primary Action Button - Contextual based on error type */}
                  {errorCategory.severity === 'low' ? (
                    <Button
                      onClick={this.handleRetry}
                      variant="default"
                      className="bg-green-600 hover:bg-green-700 text-white"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Fix & Continue
                    </Button>
                  ) : errorCategory.type === 'network' || errorCategory.type === 'timeout' ? (
                    <Button
                      onClick={() => {
                        this.handleRetry();
                        this.handleAutoRetry();
                      }}
                      variant="default"
                      className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Auto-Retry
                    </Button>
                  ) : (
                    <Button onClick={this.handleRetry} variant="ghost">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Try Again
                    </Button>
                  )}

                  {/* Secondary Actions */}
                  <Button onClick={this.handleReload} variant="ghost">
                    Full Reload
                  </Button>

                  {/* Report Bug - Only show for high severity or persistent issues */}
                  {(errorCategory.severity === 'high' || !this.state.bugContext) && (
                    <Button
                      onClick={this.handleReportBug}
                      className="bg-red-600 hover:bg-red-700 text-white"
                      disabled={!this.state.bugContext}
                    >
                      <Bug className="w-4 h-4 mr-2" />
                      Report Issue
                    </Button>
                  )}
                </div>

                {/* Auto-retry indicator for network/timeout errors */}
                {(errorCategory.type === 'network' || errorCategory.type === 'timeout') && (
                  <div className="mt-4 text-center">
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      🔄 Auto-retrying in 3 seconds...
                    </p>
                  </div>
                )}

                {/* Help Text */}
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-6">
                  If this keeps happening, please report the bug so we can fix
                  it.
                </p>
              </div>
            </Card>
          </div>

          {/* Bug Report Modal */}
          {this.state.bugContext && (
            <BugReportModal
              isOpen={this.state.showBugReport}
              onClose={this.handleCloseBugReport}
              context={this.state.bugContext}
            />
          )}
        </>
      );
    }

    return this.props.children;
  }
}
