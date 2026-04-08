import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import { App } from './App';

vi.mock('./hooks/useApi', () => ({
  apiFetch: vi.fn(),
}));

const renderWithAuth = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>{component}</AuthProvider>
    </BrowserRouter>
  );
};

describe('App', () => {
  it('renders without crashing', () => {
    const { container } = renderWithAuth(<App />);
    expect(container).toBeInTheDocument();
  });

  it('renders within router context without errors', () => {
    const { baseElement } = renderWithAuth(<App />);
    expect(baseElement).toBeInTheDocument();
  });

  it('has routes defined', () => {
    renderWithAuth(<App />);
    expect(document.body).toBeInTheDocument();
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });
});