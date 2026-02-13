import React from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import PropTypes from 'prop-types';

ChartJS.register(ArcElement, Tooltip, Legend);

const ResultsParams = ({ result, onReset }) => {
    const isReal = result.label === 'Real';
    const confidencePercent = Math.round(parseFloat(result.confidence) * 100); // Confidence comes as "0.95" string or float
    const accentHex = isReal ? '#10b981' : '#ef4444';

    const chartData = {
        labels: ['Confidence', 'Remaining'],
        datasets: [
            {
                data: [confidencePercent, 100 - confidencePercent],
                backgroundColor: [accentHex, 'rgba(255, 255, 255, 0.05)'],
                borderWidth: 0,
                borderRadius: 10,
            },
        ],
    };

    const chartOptions = {
        cutout: '85%',
        plugins: {
            legend: { display: false },
            tooltip: { enabled: false },
        },
        responsive: true,
        maintainAspectRatio: false,
    };

    return (
        <div className={`glass-panel result-card ${isReal ? 'real-border' : 'fake-border'} animate-[fadeInUp_0.5s_ease-out] p-6 md:p-12 mb-12`}>
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
                <div className="md:col-span-7">
                    <div className="flex items-center mb-8">
                        <div className="w-16 h-16 rounded-full flex items-center justify-center mr-6" style={{ background: `${accentHex}20` }}>
                            <i className={`bi ${isReal ? 'bi-patch-check-fill' : 'bi-shield-exclamation'} text-4xl`} style={{ color: accentHex }}></i>
                        </div>
                        <div>
                            <h6 className="text-slate-400 uppercase text-xs font-bold mb-1 tracking-wider">AI Verdict</h6>
                            <h2 className="text-3xl font-bold mb-0">{result.label} Content</h2>
                        </div>
                    </div>

                    <div className="mb-8">
                        <div className="flex justify-between mb-2">
                            <span className="text-slate-400 text-sm font-medium">Confidence Score</span>
                            <span className="font-bold" style={{ color: accentHex }}>{confidencePercent}%</span>
                        </div>
                        <div className="bg-white/10 h-2 rounded-full overflow-hidden">
                            <div
                                className="h-full rounded-full transition-all duration-1000 ease-out"
                                style={{
                                    width: `${confidencePercent}%`,
                                    background: accentHex,
                                    boxShadow: `0 0 10px ${accentHex}60`
                                }}
                            ></div>
                        </div>
                    </div>

                    <div className="mb-8">
                        <h6 className="text-slate-400 uppercase text-xs font-bold mb-4 tracking-wider">AI Explanation</h6>
                        <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
                            <p className="mb-0 text-slate-200 leading-relaxed text-lg font-light">{result.explanation}</p>
                        </div>
                    </div>
                </div>

                <div className="md:col-span-5 flex justify-center">
                    <div className="relative w-48 h-48">
                        <Doughnut data={chartData} options={chartOptions} />
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
                            <h3 className="text-4xl font-bold mb-0 leading-none">{confidencePercent}%</h3>
                            <span className="text-slate-400 text-sm font-medium">Match</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="mt-8 pt-8 border-t border-slate-700/30 flex justify-between items-center">
                <span className="text-slate-400 text-sm flex items-center">
                    <i className="bi bi-clock-history mr-2"></i> Analysis complete
                </span>
                <button
                    onClick={onReset}
                    className="px-6 py-2 border border-slate-600 rounded-full text-slate-300 hover:bg-slate-700 hover:text-white transition-colors text-sm font-medium"
                >
                    Reset Analyzer
                </button>
            </div>
        </div>
    );
};

ResultsParams.propTypes = {
    result: PropTypes.shape({
        label: PropTypes.string,
        confidence: PropTypes.any,
        explanation: PropTypes.string,
    }),
    onReset: PropTypes.func,
};

export default ResultsParams;
