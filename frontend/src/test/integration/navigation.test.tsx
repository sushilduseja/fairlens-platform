import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../hooks/useAuth';
import { LayoutShell } from '../../components/LayoutShell';
import { LoginPage } from '../../pages/LoginPage';
import { RegisterPage } from '../../pages/RegisterPage';

vi.mock('../../hooks/useApi', () => ({
  apiFetch: vi.fn().mockResolvedValue(null),
  AuthError: class AuthError extends Error {
    constructor(message: string) {
      super(message);
      this.name = 'AuthError';
    }
  },
}));

const renderWithAuth = async (component: React.ReactElement) => {
  const renderResult = render(
    <BrowserRouter>
      <AuthProvider>{component}</AuthProvider>
    </BrowserRouter>
  );

  await waitFor(() => {
    const loadingElement = renderResult.container.querySelector('.auth-container');
    return !loadingElement || loadingElement.textContent !== 'Loading...';
  });

  return renderResult;
};

describe('Navigation Integration', () => {
  it('Login page contains form inputs and button', async () => {
    await renderWithAuth(<LoginPage />);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('Register page contains form inputs and button', async () => {
    await renderWithAuth(<RegisterPage />);
    
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('LayoutShell has proper navigation structure', async () => {
    await renderWithAuth(<LayoutShell />);
    
    const navLinks = document.querySelectorAll('.sidebar-nav a');
    expect(navLinks.length).toBe(3);
    
    expect(navLinks[0]).toHaveTextContent('Dashboard');
    expect(navLinks[1]).toHaveTextContent('New Audit');
    expect(navLinks[2]).toHaveTextContent('Metrics');
  });

  it('Brand link points to home', async () => {
    await renderWithAuth(<LayoutShell />);
    
    const brandLink = document.querySelector('.brand-link');
    expect(brandLink).toHaveAttribute('href', '/');
  });

  it('Unmatched routes render without crashing', async () => {
    render(
      <MemoryRouter initialEntries={['/invalid-route']}>
        <AuthProvider>
          <LayoutShell />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(document.querySelector('.sidebar')).toBeInTheDocument();
    });
  });
});

describe('Page Content', () => {
  it('Login page has correct heading', async () => {
    await renderWithAuth(<LoginPage />);
    expect(screen.getByRole('heading', { name: 'Welcome Back' })).toBeInTheDocument();
  });

  it('Register page has correct heading', async () => {
    await renderWithAuth(<RegisterPage />);
    expect(screen.getByRole('heading', { name: 'Create Account' })).toBeInTheDocument();
  });
});