import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '../components/StatusBadge';

describe('StatusBadge', () => {
  it('renders PASS status correctly', () => {
    render(<StatusBadge value="PASS" />);
    expect(screen.getByText('PASS')).toBeInTheDocument();
  });

  it('renders FAIL status correctly', () => {
    render(<StatusBadge value="FAIL" />);
    expect(screen.getByText('FAIL')).toBeInTheDocument();
  });

  it('renders CONDITIONAL_PASS as CONDITIONAL', () => {
    render(<StatusBadge value="CONDITIONAL_PASS" />);
    expect(screen.getByText('CONDITIONAL_PASS')).toBeInTheDocument();
  });

  it('renders queued status correctly', () => {
    render(<StatusBadge value="queued" />);
    expect(screen.getByText('queued')).toBeInTheDocument();
  });

  it('renders processing status correctly', () => {
    render(<StatusBadge value="processing" />);
    expect(screen.getByText('processing')).toBeInTheDocument();
  });

  it('renders completed status correctly', () => {
    render(<StatusBadge value="completed" />);
    expect(screen.getByText('completed')).toBeInTheDocument();
  });

  it('renders failed status correctly', () => {
    render(<StatusBadge value="failed" />);
    expect(screen.getByText('failed')).toBeInTheDocument();
  });

  it('handles null value', () => {
    render(<StatusBadge value={null} />);
    expect(screen.getByText('unknown')).toBeInTheDocument();
  });

  it('handles undefined value', () => {
    render(<StatusBadge value={undefined} />);
    expect(screen.getByText('unknown')).toBeInTheDocument();
  });

  it('applies large class when large prop is true', () => {
    render(<StatusBadge value="PASS" large />);
    const badge = screen.getByText('PASS');
    expect(badge).toHaveClass('badge-large');
  });

  it('normalizes conditional_pass to CONDITIONAL', () => {
    render(<StatusBadge value="conditional_pass" />);
    expect(screen.getByText('CONDITIONAL')).toBeInTheDocument();
  });
});