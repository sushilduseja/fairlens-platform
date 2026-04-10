import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../hooks/useAuth';
import { apiFetch } from '../hooks/useApi';
import { RegisterPage } from '../pages/RegisterPage';

vi.mock('../hooks/useApi', () => ({
  apiFetch: vi.fn().mockResolvedValue(null),
  AuthError: class AuthError extends Error {
    constructor(message: string) {
      super(message);
      this.name = 'AuthError';
    }
  },
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>{component}</AuthProvider>
    </BrowserRouter>
  );
};

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.getItem = vi.fn().mockReturnValue(null);
    localStorage.setItem = vi.fn();
    vi.stubGlobal('navigator', {
      clipboard: {
        writeText: vi.fn(),
      },
    });
  });

  it('renders registration form with name, email and password fields', () => {
    renderWithRouter(<RegisterPage />);
    
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i, { selector: 'input' })).toBeInTheDocument();
  });

  it('renders Create Account button', () => {
    renderWithRouter(<RegisterPage />);
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('renders link to login page', () => {
    renderWithRouter(<RegisterPage />);
    expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument();
  });

  it('renders create account heading', () => {
    renderWithRouter(<RegisterPage />);
    expect(screen.getByRole('heading', { name: 'Create Account' })).toBeInTheDocument();
  });

  it('shows success screen with API key after registration', async () => {
    (apiFetch as vi.Mock).mockResolvedValue({
      user_id: 'user-123',
      api_key: 'fl_testapikey123456789',
    });
    
    renderWithRouter(<RegisterPage />);
    
    const nameInput = screen.getByLabelText(/full name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i, { selector: 'input' });
    const submitButton = screen.getByRole('button', { name: /create account/i });
    
    await userEvent.setup().type(nameInput, 'Test User');
    await userEvent.setup().type(emailInput, 'test@example.com');
    await userEvent.setup().type(passwordInput, 'password123');
    await userEvent.setup().click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/account created/i)).toBeInTheDocument();
    });
  });

  it('shows error message on failed registration', async () => {
    (apiFetch as vi.Mock).mockRejectedValue(new Error('Email already registered'));
    
    renderWithRouter(<RegisterPage />);
    
    const nameInput = screen.getByLabelText(/full name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i, { selector: 'input' });
    const submitButton = screen.getByRole('button', { name: /create account/i });
    
    await userEvent.setup().type(nameInput, 'Test User');
    await userEvent.setup().type(emailInput, 'test@example.com');
    await userEvent.setup().type(passwordInput, 'password123');
    await userEvent.setup().click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/email already registered/i)).toBeInTheDocument();
    });
  });

  it('validates password minimum length', () => {
    renderWithRouter(<RegisterPage />);
    
    const passwordInput = screen.getByLabelText(/password/i, { selector: 'input' });
    expect(passwordInput).toHaveAttribute('minLength', '8');
  });

  it('has link to login page', () => {
    renderWithRouter(<RegisterPage />);
    const loginLink = screen.getByRole('link', { name: /sign in/i });
    expect(loginLink).toHaveAttribute('href', '/login');
  });
});