import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { credentialsService } from '../../../archon-ui-main/src/services/credentialsService';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('Credentials Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('getCredentials', () => {
    it('returns null when no credentials are stored', () => {
      localStorageMock.getItem.mockReturnValue(null);
      const credentials = credentialsService.getCredentials();
      expect(credentials).toBeNull();
    });

    it('returns stored credentials when available', () => {
      const mockCredentials = {
        openai: 'test-openai-key',
        anthropic: 'test-anthropic-key',
        grok: 'test-grok-key',
      };
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockCredentials));
      const credentials = credentialsService.getCredentials();
      expect(credentials).toEqual(mockCredentials);
    });

    it('handles malformed stored credentials gracefully', () => {
      localStorageMock.getItem.mockReturnValue('invalid-json');
      const credentials = credentialsService.getCredentials();
      expect(credentials).toBeNull();
    });
  });

  describe('setCredentials', () => {
    it('stores credentials in localStorage', () => {
      const testCredentials = {
        openai: 'new-openai-key',
        anthropic: 'new-anthropic-key',
      };
      
      credentialsService.setCredentials(testCredentials);
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'archon-credentials',
        JSON.stringify(testCredentials)
      );
    });

    it('overwrites existing credentials', () => {
      const existingCredentials = { openai: 'old-key' };
      const newCredentials = { openai: 'new-key' };
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(existingCredentials));
      credentialsService.setCredentials(newCredentials);
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'archon-credentials',
        JSON.stringify(newCredentials)
      );
    });
  });

  describe('updateCredentials', () => {
    it('updates specific credential without affecting others', () => {
      const existingCredentials = {
        openai: 'existing-openai',
        anthropic: 'existing-anthropic',
      };
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(existingCredentials));
      
      credentialsService.updateCredentials('openai', 'updated-openai');
      
      const expectedCredentials = {
        ...existingCredentials,
        openai: 'updated-openai',
      };
      
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'archon-credentials',
        JSON.stringify(expectedCredentials)
      );
    });

    it('creates new credentials object if none exist', () => {
      localStorageMock.getItem.mockReturnValue(null);
      
      credentialsService.updateCredentials('openai', 'new-openai');
      
      const expectedCredentials = { openai: 'new-openai' };
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'archon-credentials',
        JSON.stringify(expectedCredentials)
      );
    });
  });

  describe('removeCredentials', () => {
    it('removes specific credential', () => {
      const existingCredentials = {
        openai: 'existing-openai',
        anthropic: 'existing-anthropic',
      };
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(existingCredentials));
      
      credentialsService.removeCredentials('openai');
      
      const expectedCredentials = { anthropic: 'existing-anthropic' };
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'archon-credentials',
        JSON.stringify(expectedCredentials)
      );
    });

    it('removes all credentials when no specific key provided', () => {
      credentialsService.removeCredentials();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('archon-credentials');
    });
  });

  describe('hasCredentials', () => {
    it('returns false when no credentials exist', () => {
      localStorageMock.getItem.mockReturnValue(null);
      expect(credentialsService.hasCredentials()).toBe(false);
    });

    it('returns true when credentials exist', () => {
      const mockCredentials = { openai: 'test-key' };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockCredentials));
      expect(credentialsService.hasCredentials()).toBe(true);
    });

    it('returns false for empty credentials object', () => {
      localStorageMock.getItem.mockReturnValue(JSON.stringify({}));
      expect(credentialsService.hasCredentials()).toBe(false);
    });
  });

  describe('getBaseUrl', () => {
    it('returns default base URL when not configured', () => {
      expect(credentialsService.baseUrl).toBe('http://localhost:8181');
    });

    it('returns configured base URL when available', () => {
      const mockCredentials = { baseUrl: 'https://custom-server.com' };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockCredentials));
      
      // Re-initialize to pick up new credentials
      const service = credentialsService;
      expect(service.baseUrl).toBe('https://custom-server.com');
    });
  });

  describe('getApiKey', () => {
    it('returns null for non-existent provider', () => {
      const mockCredentials = { openai: 'test-key' };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockCredentials));
      
      const apiKey = credentialsService.getApiKey('nonexistent');
      expect(apiKey).toBeNull();
    });

    it('returns API key for existing provider', () => {
      const mockCredentials = { openai: 'test-openai-key' };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockCredentials));
      
      const apiKey = credentialsService.getApiKey('openai');
      expect(apiKey).toBe('test-openai-key');
    });
  });
});
