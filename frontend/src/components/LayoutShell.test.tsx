import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../hooks/useAuth';
import { LayoutShell } from '../components/LayoutShell';

vi.mock('../hooks/useApi', () => ({
  apiFetch: vi.fn(),
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>{component}</AuthProvider>
    </BrowserRouter>
  );
};

describe('LayoutShell', () => {
  it('renders the FairLens brand', () => {
    renderWithRouter(<LayoutShell />);
    expect(screen.getByText('FairLens')).toBeInTheDocument();
  });

  it('renders Dashboard navigation link', () => {
    renderWithRouter(<LayoutShell />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders New Audit navigation link', () => {
    renderWithRouter(<LayoutShell />);
    expect(screen.getByText('New Audit')).toBeInTheDocument();
  });

  it('renders Metrics navigation link', () => {
    renderWithRouter(<LayoutShell />);
    expect(screen.getByText('Metrics')).toBeInTheDocument();
  });

  it('renders version badge', () => {
    renderWithRouter(<LayoutShell />);
    expect(screen.getByText('v0.1.0')).toBeInTheDocument();
  });

  it('renders sidebar with app-shell class', () => {
    renderWithRouter(<LayoutShell />);
    const appShell = document.querySelector('.app-shell');
    expect(appShell).toBeInTheDocument();
  });

  it('renders sidebar element', () => {
    renderWithRouter(<LayoutShell />);
    const sidebar = document.querySelector('.sidebar');
    expect(sidebar).toBeInTheDocument();
  });

  it('renders main content area', () => {
    renderWithRouter(<LayoutShell />);
    const content = document.querySelector('.content');
    expect(content).toBeInTheDocument();
  });
});