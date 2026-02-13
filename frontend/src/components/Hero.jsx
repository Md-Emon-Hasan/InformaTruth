import React from 'react';

const Hero = () => {
    return (
        <div className="text-center mb-12 animate-[fadeInDown_1s_ease-out]">
            <h1 className="text-5xl md:text-6xl font-bold mb-6 tracking-tight">
                Detect Truth with <span className="gradient-text">Precision</span>
            </h1>
            <p className="text-slate-400 text-lg md:text-xl mx-auto max-w-2xl leading-relaxed">
                Advanced Multi-Agent system powered by fine-tuned RoBERTa and FLAN-T5 for news authenticity analysis.
            </p>
        </div>
    );
};

export default Hero;
