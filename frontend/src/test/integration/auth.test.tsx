import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../hooks/useAuth';
import { LoginPage } from '../../pages/LoginPage';
import { RegisterPage } from '../../pages/RegisterPage';
import { LayoutShell } from '../../components/LayoutShell';

vi.mock('../../hooks/useApi', () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../../hooks/useApi';

const renderWithAuth = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>{component}</AuthProvider>
    </BrowserRouter>
  );
};

describe('Auth Flow Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.getItem = vi.fn().mockReturnValue(null);
    localStorage.setItem = vi.fn();
  });

  it('login shows error on invalid credentials', async () => {
    (apiFetch as vi.Mock).mockRejectedValue(new Error('Invalid credentials'));
    
    renderWithAuth(<LoginPage />);
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await userEvent.setup().type(emailInput, 'wrong@example.com');
    await userEvent.setup().type(passwordInput, 'wrongpassword');
    await userEvent.setup().click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('register shows error on failed registration', async () => {
    (apiFetch as vi.Mock).mockRejectedValue(new Error('Email already exists'));
    
    renderWithAuth(<RegisterPage />);
    
    const nameInput = screen.getByLabelText(/full name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /create account/i });
    
    await userEvent.setup().type(nameInput, 'Test User');
    await userEvent.setup().type(emailInput, 'existing@example.com');
    await userEvent.setup().type(passwordInput, 'password123');
    await userEvent.setup().click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/email already exists/i)).toBeInTheDocument();
    });
  });
});

describe('Layout Integration', () => {
  it('LayoutShell renders with all navigation items', () => {
    renderWithAuth(<LayoutShell />);
    
    expect(screen.getByText('FairLens')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('New Audit')).toBeInTheDocument();
    expect(screen.getByText('Metrics')).toBeInTheDocument();
    expect(screen.getByText('v0.1.0')).toBeInTheDocument();
  });

  it('LayoutShell has sidebar structure', () => {
    renderWithAuth(<LayoutShell />);
    
    expect(document.querySelector('.sidebar')).toBeInTheDocument();
    expect(document.querySelector('.sidebar-nav')).toBeInTheDocument();
    expect(document.querySelector('.content')).toBeInTheDocument();
  });
});