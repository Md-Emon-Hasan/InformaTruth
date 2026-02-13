import { render, screen } from '@testing-library/react';
import App from './App';
import { describe, it, expect, vi } from 'vitest';

vi.mock('pdfjs-dist', () => ({
    GlobalWorkerOptions: { workerSrc: '' },
    getDocument: () => ({ promise: Promise.resolve({ numPages: 0 }) }),
    version: '1.0.0',
}));

describe('App Component', () => {
    it('renders Navbar with brand name', () => {
        render(<App />);
        const brandElements = screen.getAllByText(/InformaTruth/i);
        expect(brandElements.length).toBeGreaterThan(0);
        expect(brandElements[0]).toBeInTheDocument();
    });

    it('renders Hero section', () => {
        render(<App />);
        const heroText = screen.getByText(/Detect Truth/i);
        expect(heroText).toBeInTheDocument();
    });

    it('renders AnalysisForm', () => {
        render(<App />);
        const formHeader = screen.getByText(/Analyzer Engine/i);
        expect(formHeader).toBeInTheDocument();
    });

    it('renders Footer', () => {
        render(<App />);
        const footerElements = screen.getAllByText(/InformaTruth AI/i);
        expect(footerElements.length).toBeGreaterThan(0);
        // We expect at least one to be in the footer/document
        const footerInstance = footerElements.find(el => el.closest('footer'));
        expect(footerInstance).toBeInTheDocument();
    });
});
