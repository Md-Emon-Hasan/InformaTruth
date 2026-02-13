import React from 'react';

const Navbar = () => {
    return (
        <nav className="navbar-glass sticky top-0 z-50 py-4">
            <div className="container mx-auto px-4 flex justify-between items-center">
                <a className="flex items-center gap-2 group" href="/">
                    <div className="brand-logo drop-shadow-[0_0_8px_var(--primary)] text-primary">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor"
                            className="bi bi-shield-lock-fill" viewBox="0 0 16 16">
                            <path fillRule="evenodd"
                                d="M8 0c-.69 0-1.843.265-2.928.56-1.11.3-2.229.655-2.887.87a1.54 1.54 0 0 0-1.044 1.262c-.596 4.477.787 7.795 2.465 9.99a11.777 11.777 0 0 0 2.517 2.453c.386.273.744.482 1.048.625.28.132.581.24.829.24s.548-.108.829-.24c.304-.143.662-.352 1.048-.625a11.775 11.775 0 0 0 2.517-2.453c1.678-2.195 3.061-5.513 2.465-9.99a1.541 1.541 0 0 0-1.044-1.263 62.467 62.467 0 0 0-2.887-.87C9.843.266 8.69 0 8 0m0 5a1.5 1.5 0 0 1 .5 2.915V10a.5.5 0 0 1-1 0V7.915A1.5 1.5 0 0 1 8 5" />
                        </svg>
                    </div>
                    <span className="text-xl font-bold gradient-text">InformaTruth AI</span>
                </a>

                <div className="hidden lg:flex items-center gap-6">
                    <a className="text-slate-400 font-medium hover:text-white hover:drop-shadow-[0_0_10px_rgba(139,92,246,0.5)] transition-colors active text-white" href="/">Dashboard</a>
                    <a className="text-slate-400 font-medium hover:text-white hover:drop-shadow-[0_0_10px_rgba(139,92,246,0.5)] transition-colors" href="#">Research</a>
                    <a className="text-slate-400 font-medium hover:text-white hover:drop-shadow-[0_0_10px_rgba(139,92,246,0.5)] transition-colors" target="_blank" href="http://127.0.0.1:8000/docs">API Docs</a>
                </div>

                <button className="lg:hidden text-white text-2xl">
                    <i className="bi bi-list"></i>
                </button>
            </div>
        </nav>
    );
};

export default Navbar;
