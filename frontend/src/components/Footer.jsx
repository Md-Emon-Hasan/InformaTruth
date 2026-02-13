import React from 'react';

const Footer = () => {
    return (
        <footer className="py-12 border-t border-slate-700/30 mt-12 bg-slate-900/50 backdrop-blur-sm">
            <div className="container mx-auto text-center px-4">
                <h5 className="font-bold mb-6 gradient-text text-xl">InformaTruth AI</h5>
                <div className="flex justify-center mb-6 space-x-2">
                    <a href="https://github.com/Md-Emon-Hasan" className="social-link w-10 h-10 inline-flex items-center justify-center rounded-full bg-white/5 mx-2 text-xl text-slate-400 transition-all duration-300 hover:bg-violet-500 hover:text-white hover:-translate-y-1"><i className="bi bi-github"></i></a>
                    <a href="https://www.linkedin.com/in/md-emon-hasan-695483237/" className="social-link w-10 h-10 inline-flex items-center justify-center rounded-full bg-white/5 mx-2 text-xl text-slate-400 transition-all duration-300 hover:bg-violet-500 hover:text-white hover:-translate-y-1"><i className="bi bi-linkedin"></i></a>
                    <a href="https://www.facebook.com/mdemon.hasan2001/" className="social-link w-10 h-10 inline-flex items-center justify-center rounded-full bg-white/5 mx-2 text-xl text-slate-400 transition-all duration-300 hover:bg-violet-500 hover:text-white hover:-translate-y-1"><i className="bi bi-facebook"></i></a>
                    <a href="https://wa.me/8801834363533" className="social-link w-10 h-10 inline-flex items-center justify-center rounded-full bg-white/5 mx-2 text-xl text-slate-400 transition-all duration-300 hover:bg-violet-500 hover:text-white hover:-translate-y-1"><i className="bi bi-whatsapp"></i></a>
                    <a href="mailto:emon.mlengineer@gmail.com" className="social-link w-10 h-10 inline-flex items-center justify-center rounded-full bg-white/5 mx-2 text-xl text-slate-400 transition-all duration-300 hover:bg-violet-500 hover:text-white hover:-translate-y-1"><i className="bi bi-envelope-fill"></i></a>
                </div>
                <p className="text-slate-400 text-sm mb-1">© 2025 InformaTruth System. All labels are AI-generated estimates.</p>
                <p className="text-slate-400 text-sm">Crafted with precision by <span className="text-white font-medium">Md Emon Hasan</span></p>
            </div>
        </footer>
    );
};

export default Footer;
