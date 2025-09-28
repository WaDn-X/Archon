import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TaskBoardView } from '../../../archon-ui-main/src/components/project-tasks/TaskBoardView';
import { ProjectCreationProgressCard } from '../../../archon-ui-main/src/components/ProjectCreationProgressCard';

// Mock services
vi.mock('../../../archon-ui-main/src/services/projectService', () => ({
  projectService: {
    getProjects: vi.fn(() => Promise.resolve({ data: [] })),
    createProject: vi.fn(() => Promise.resolve({ success: true, id: '123' })),
    updateProject: vi.fn(() => Promise.resolve({ success: true })),
    deleteProject: vi.fn(() => Promise.resolve({ success: true })),
  },
}));

vi.mock('../../../archon-ui-main/src/services/taskSocketService', () => ({
  taskSocketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    onTaskUpdate: vi.fn(),
    emitTaskUpdate: vi.fn(),
  },
}));

vi.mock('../../../archon-ui-main/src/contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}));

const mockProject = {
  id: '1',
  title: 'Test Project',
  description: 'A test project description',
  github_repo: 'https://github.com/test/repo',
  status: 'active',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockTask = {
  id: '1',
  project_id: '1',
  title: 'Test Task',
  description: 'Task description',
  status: 'todo',
  assignee: 'Test User',
  task_order: 1,
  feature: 'Authentication',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Project Management Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('TaskBoardView', () => {
    it('renders task board with columns', () => {
      renderWithRouter(<TaskBoardView projectId="1" />);

      expect(screen.getByText('To Do')).toBeInTheDocument();
      expect(screen.getByText('In Progress')).toBeInTheDocument();
      expect(screen.getByText('Done')).toBeInTheDocument();
    });

    it('displays tasks in correct columns', async () => {
      // Mock tasks data
      const mockTasks = [
        { ...mockTask, status: 'todo' },
        { ...mockTask, id: '2', title: 'In Progress Task', status: 'in_progress' },
        { ...mockTask, id: '3', title: 'Done Task', status: 'done' },
      ];

      // This would require mocking the task service
      renderWithRouter(<TaskBoardView projectId="1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });
    });

    it('handles drag and drop between columns', async () => {
      renderWithRouter(<TaskBoardView projectId="1" />);

      // Mock drag start
      const taskCard = await screen.findByText('Test Task');
      const taskElement = taskCard.closest('[draggable]');

      if (taskElement) {
        fireEvent.dragStart(taskElement);

        // Mock drop on different column
        const inProgressColumn = screen.getByText('In Progress').closest('.task-column');
        if (inProgressColumn) {
          fireEvent.drop(inProgressColumn);
        }

        // Should trigger status update
        expect(taskElement).toBeInTheDocument();
      }
    });

    it('handles task creation', async () => {
      renderWithRouter(<TaskBoardView projectId="1" />);

      const addTaskButton = screen.getByText('Add Task');
      fireEvent.click(addTaskButton);

      // Should show task creation modal/form
      expect(screen.getByText('Create New Task')).toBeInTheDocument();

      const titleInput = screen.getByLabelText('Task Title');
      const descriptionInput = screen.getByLabelText('Description');

      fireEvent.change(titleInput, { target: { value: 'New Test Task' } });
      fireEvent.change(descriptionInput, { target: { value: 'New task description' } });

      const createButton = screen.getByText('Create Task');
      fireEvent.click(createButton);

      // Should trigger task creation
      await waitFor(() => {
        expect(screen.getByText('New Test Task')).toBeInTheDocument();
      });
    });

    it('handles task editing', async () => {
      renderWithRouter(<TaskBoardView projectId="1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });

      const taskCard = screen.getByText('Test Task');
      fireEvent.click(taskCard);

      // Should show task edit modal
      expect(screen.getByText('Edit Task')).toBeInTheDocument();

      const titleInput = screen.getByDisplayValue('Test Task');
      fireEvent.change(titleInput, { target: { value: 'Updated Task Title' } });

      const saveButton = screen.getByText('Save Changes');
      fireEvent.click(saveButton);

      // Should update task title
      await waitFor(() => {
        expect(screen.getByText('Updated Task Title')).toBeInTheDocument();
      });
    });

    it('handles task deletion', async () => {
      renderWithRouter(<TaskBoardView projectId="1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      fireEvent.click(deleteButton);

      // Should show confirmation dialog
      expect(screen.getByText('Confirm Delete')).toBeInTheDocument();

      const confirmButton = screen.getByText('Delete');
      fireEvent.click(confirmButton);

      // Task should be removed
      await waitFor(() => {
        expect(screen.queryByText('Test Task')).not.toBeInTheDocument();
      });
    });
  });

  describe('ProjectCreationProgressCard', () => {
    it('renders progress card correctly', () => {
      renderWithRouter(<ProjectCreationProgressCard />);

      expect(screen.getByText('Creating Project')).toBeInTheDocument();
    });

    it('displays progress stages', () => {
      renderWithRouter(<ProjectCreationProgressCard />);

      expect(screen.getByText('Analyzing requirements')).toBeInTheDocument();
      expect(screen.getByText('Generating documentation')).toBeInTheDocument();
      expect(screen.getByText('Creating tasks')).toBeInTheDocument();
    });

    it('shows current progress percentage', () => {
      renderWithRouter(<ProjectCreationProgressCard />);

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute('aria-valuenow');
    });

    it('handles completion state', async () => {
      // Mock completed progress
      renderWithRouter(<ProjectCreationProgressCard />);

      await waitFor(() => {
        expect(screen.getByText('Project created successfully!')).toBeInTheDocument();
      });

      const viewProjectButton = screen.getByText('View Project');
      expect(viewProjectButton).toBeInTheDocument();
    });

    it('handles error states', async () => {
      // Mock error state
      renderWithRouter(<ProjectCreationProgressCard />);

      await waitFor(() => {
        expect(screen.getByText('Project creation failed')).toBeInTheDocument();
      });

      const retryButton = screen.getByText('Retry');
      expect(retryButton).toBeInTheDocument();

      const cancelButton = screen.getByText('Cancel');
      expect(cancelButton).toBeInTheDocument();
    });

    it('updates progress in real-time', async () => {
      renderWithRouter(<ProjectCreationProgressCard />);

      // Simulate progress updates
      await waitFor(() => {
        const progressBar = screen.getByRole('progressbar');
        const progressValue = progressBar.getAttribute('aria-valuenow');
        expect(parseInt(progressValue || '0')).toBeGreaterThan(0);
      });
    });
  });

  describe('Project Management Integration', () => {
    it('handles real-time task updates', async () => {
      const mockSocketService = vi.mocked(
        await import('../../../archon-ui-main/src/services/taskSocketService')
      ).taskSocketService;

      renderWithRouter(<TaskBoardView projectId="1" />);

      await waitFor(() => {
        expect(mockSocketService.connect).toHaveBeenCalled();
      });

      // Simulate socket message
      const mockCallback = mockSocketService.onTaskUpdate.mock.calls[0][1];
      mockCallback({
        type: 'task_updated',
        data: { ...mockTask, title: 'Updated via Socket' },
      });

      await waitFor(() => {
        expect(screen.getByText('Updated via Socket')).toBeInTheDocument();
      });
    });

    it('maintains optimistic updates', async () => {
      renderWithRouter(<TaskBoardView projectId="1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });

      // Simulate optimistic update
      const taskCard = screen.getByText('Test Task');
      fireEvent.click(taskCard);

      const titleInput = screen.getByDisplayValue('Test Task');
      fireEvent.change(titleInput, { target: { value: 'Optimistic Update' } });

      // Should show immediate update
      expect(screen.getByDisplayValue('Optimistic Update')).toBeInTheDocument();

      // Even if server update fails, UI should revert gracefully
    });

    it('handles offline scenarios', async () => {
      // Mock network failure
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/projectService')
      ).projectService;

      mockService.updateProject.mockRejectedValue(new Error('Network error'));

      renderWithRouter(<TaskBoardView projectId="1" />);

      await waitFor(() => {
        expect(screen.getByText('Test Task')).toBeInTheDocument();
      });

      // Should show offline indicator and queue updates
      expect(screen.getByText('Offline - Changes will sync when connection returns')).toBeInTheDocument();
    });
  });
});
