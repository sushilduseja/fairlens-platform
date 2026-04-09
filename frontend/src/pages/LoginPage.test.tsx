import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../hooks/useAuth';
import { apiFetch } from '../hooks/useApi';
import { LoginPage } from '../pages/LoginPage';

vi.mock('../hooks/useApi', () => ({
  apiFetch: vi.fn().mockImplementation((url) => {
    if (url === '/auth/me') return Promise.resolve(null);
    return Promise.resolve(null);
  }),
  AuthError: class AuthError extends Error {
    constructor(message: string) {
      super(message);
      this.name = 'AuthError';
    }
  },
}));

const renderWithRouter = async (component: React.ReactElement) => {
  const renderResult = render(
    <BrowserRouter>
      <AuthProvider>{component}</AuthProvider>
    </BrowserRouter>
  );
  
  // Wait for auth initialization to complete
  await waitFor(() => {
    const loadingElement = renderResult.container.querySelector('.auth-container');
    return !loadingElement || loadingElement.textContent !== 'Loading...';
  });
  
  return renderResult;
};

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.getItem = vi.fn().mockReturnValue(null);
  });

  it('renders login form with email and password fields', async () => {
    await renderWithRouter(<LoginPage />);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('renders Sign In button', async () => {
    await renderWithRouter(<LoginPage />);
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('renders link to register page', async () => {
    await renderWithRouter(<LoginPage />);
    expect(screen.getByRole('link', { name: /create an account/i })).toBeInTheDocument();
  });

  it('renders welcome heading', async () => {
    await renderWithRouter(<LoginPage />);
    expect(screen.getByRole('heading', { name: 'Welcome Back' })).toBeInTheDocument();
  });

  it('updates email state on input change', async () => {
    const user = userEvent.setup();
    await renderWithRouter(<LoginPage />);
    
    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 'test@example.com');
    
    expect(emailInput).toHaveValue('test@example.com');
  });

  it('updates password state on input change', async () => {
    const user = userEvent.setup();
    await renderWithRouter(<LoginPage />);
    
    const passwordInput = screen.getByLabelText(/password/i);
    await user.type(passwordInput, 'password123');
    
    expect(passwordInput).toHaveValue('password123');
  });

  it('shows error message on failed login', async () => {
    const user = userEvent.setup();
    (apiFetch as vi.Mock).mockRejectedValue(new Error('Invalid credentials'));
    
    await renderWithRouter(<LoginPage />);
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('shows loading state during submission', async () => {
    let resolveFn: (value: unknown) => void;
    (apiFetch as vi.Mock).mockImplementation((url) => {
      if (url === '/auth/me') return Promise.resolve(null);
      return new Promise((resolve) => {
        resolveFn = resolve;
      });
    });
    
    const user = userEvent.setup();
    await renderWithRouter(<LoginPage />);
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);
    
    expect(screen.getByRole('button', { name: /signing in/i })).toBeInTheDocument();
    
    resolveFn!({ session_token: 'token', user: { id: '1', email: 'test@example.com', name: 'Test' } });
  });

  it('has proper form structure with required attributes', async () => {
    await renderWithRouter(<LoginPage />);
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    
    expect(emailInput).toHaveAttribute('type', 'email');
    expect(emailInput).toBeRequired();
    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(passwordInput).toBeRequired();
  });
});