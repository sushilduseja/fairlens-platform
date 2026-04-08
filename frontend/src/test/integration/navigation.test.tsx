import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../hooks/useAuth';
import { LayoutShell } from '../../components/LayoutShell';
import { LoginPage } from '../../pages/LoginPage';
import { RegisterPage } from '../../pages/RegisterPage';

vi.mock('../../hooks/useApi', () => ({
  apiFetch: vi.fn(),
}));

const renderWithAuth = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>{component}</AuthProvider>
    </BrowserRouter>
  );
};

describe('Navigation Integration', () => {
  it('Login page contains form inputs and button', () => {
    renderWithAuth(<LoginPage />);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('Register page contains form inputs and button', () => {
    renderWithAuth(<RegisterPage />);
    
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('LayoutShell has proper navigation structure', () => {
    renderWithAuth(<LayoutShell />);
    
    const navLinks = document.querySelectorAll('.sidebar-nav a');
    expect(navLinks.length).toBe(3);
    
    expect(navLinks[0]).toHaveTextContent('Dashboard');
    expect(navLinks[1]).toHaveTextContent('New Audit');
    expect(navLinks[2]).toHaveTextContent('Metrics');
  });

  it('Brand link points to home', () => {
    renderWithAuth(<LayoutShell />);
    
    const brandLink = document.querySelector('.brand-link');
    expect(brandLink).toHaveAttribute('href', '/');
  });

  it('Unmatched routes render without crashing', () => {
    render(
      <MemoryRouter initialEntries={['/invalid-route']}>
        <AuthProvider>
          <LayoutShell />
        </AuthProvider>
      </MemoryRouter>
    );
    
    // Should still render without crashing
    expect(document.querySelector('.sidebar')).toBeInTheDocument();
  });
});

describe('Page Content', () => {
  it('Login page has correct heading', () => {
    renderWithAuth(<LoginPage />);
    expect(screen.getByRole('heading', { name: 'Welcome Back' })).toBeInTheDocument();
  });

  it('Register page has correct heading', () => {
    renderWithAuth(<RegisterPage />);
    expect(screen.getByRole('heading', { name: 'Create Account' })).toBeInTheDocument();
  });
});