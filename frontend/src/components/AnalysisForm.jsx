import React, { useState } from 'react';
import axios from 'axios';
import * as pdfjsLib from 'pdfjs-dist';
import ResultsParams from './ResultsParams';

// Set worker source for PDF.js - using a CDN is often easier than bundling in some setups,
// but for production, you might want to bundle the worker.
// We'll try to set it dynamically based on the version.
// Note: This relies on internet access. For offline, we'd need to copy the worker file.
pdfjsLib.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;

const AnalysisForm = () => {
    const [inputType, setInputType] = useState('text'); // text, url, pdf
    const [textInput, setTextInput] = useState('');
    const [urlInput, setUrlInput] = useState('');
    const [fileInput, setFileInput] = useState(null);
    const [fileName, setFileName] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleInputTypeChange = (type) => {
        setInputType(type);
        setResult(null);
        setError(null);
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setFileInput(file);
            setFileName(file.name);
        }
    };

    const clearFile = () => {
        setFileInput(null);
        setFileName('');
        const fileInputEl = document.getElementById('fileUpload');
        if (fileInputEl) fileInputEl.value = '';
    };

    const extractTextFromPDF = async (file) => {
        try {
            const arrayBuffer = await file.arrayBuffer();
            const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
            let fullText = '';

            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const textContent = await page.getTextContent();
                const pageText = textContent.items.map(item => item.str).join(' ');
                fullText += pageText + '\n';
            }
            return fullText;
        } catch (err) {
            console.error("PDF Extraction Error:", err);
            throw new Error("Failed to extract text from PDF.");
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);
        setError(null);

        try {
            let contentToAnalyze = '';
            let typeToSend = inputType;

            if (inputType === 'text') {
                if (!textInput.trim()) throw new Error("Please enter some text to analyze");
                contentToAnalyze = textInput;
            } else if (inputType === 'url') {
                if (!urlInput.trim()) throw new Error("Please enter a URL");
                try {
                    new URL(urlInput);
                } catch {
                    throw new Error("Invalid URL format");
                }
                contentToAnalyze = urlInput;
            } else if (inputType === 'pdf') {
                if (!fileInput) throw new Error("Please select a PDF file");
                // Extract text on frontend to send as text content (simplifying backend requirement)
                // However, backend has specific 'pdf' handler. 
                // Since 'input_handler.py' expects a file path for 'pdf' type, we cannot send 'pdf' type with text content.
                // We will send it as 'text' type but maybe prepend context or just analyze the text.
                // The prompt asked for "Same pixel to pixel". The original app sent 'pdf' type but logic was broken or local-only.
                // To make it functional, we extract text and send as 'text'.
                contentToAnalyze = await extractTextFromPDF(fileInput);
                // We send it as 'text' because our backend's 'pdf' handler expects a local file path which we can't provide from browser.
                typeToSend = 'text';
            }

            // Using relative URL, assuming proxy in Vite or standard port in Docker
            // For local dev, we might need full URL if not proxied.
            // We'll set a base URL or rely on proxy.
            // Vite config usually sets proxy. We'll assume standard localhost:8000 for now if API fails.
            const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/analyze';

            const response = await axios.post(apiUrl, {
                inputType: typeToSend,
                content: contentToAnalyze
            });

            setResult(response.data);
        } catch (err) {
            console.error("Analysis Error:", err);
            setError(err.message || "An unexpected error occurred during analysis.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="glass-panel p-6 md:p-12 animate-[fadeIn_0.5s_ease-out]">
            <div className="mb-12 text-center">
                <h4 className="font-bold mb-0 text-xl"><i className="bi bi-cpu-fill mr-2 gradient-text"></i>Analyzer Engine</h4>
                <div className="h-0.5 w-1/4 bg-violet-500 mx-auto mt-2 opacity-50"></div>
            </div>

            {!result && (
                <form onSubmit={handleSubmit} id="analysisForm">
                    {/* Input Selector */}
                    <div className="mb-8">
                        <label className="block text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Analysis Vector</label>
                        <div className="grid grid-cols-3 gap-4">
                            <label className={`cursor-pointer border border-white/10 rounded-xl p-4 flex flex-col items-center justify-center transition-all ${inputType === 'text' ? 'bg-gradient-to-br from-violet-600 to-sky-500 text-white shadow-lg shadow-violet-500/40 border-transparent' : 'text-slate-400 hover:border-slate-600 hover:text-slate-200'}`}>
                                <input type="radio" name="inputType" value="text" checked={inputType === 'text'} onChange={() => handleInputTypeChange('text')} className="hidden" />
                                <i className="bi bi-text-left text-2xl mb-1"></i>
                                <span className="text-xs font-medium">Text Content</span>
                            </label>

                            <label className={`cursor-pointer border border-white/10 rounded-xl p-4 flex flex-col items-center justify-center transition-all ${inputType === 'url' ? 'bg-gradient-to-br from-violet-600 to-sky-500 text-white shadow-lg shadow-violet-500/40 border-transparent' : 'text-slate-400 hover:border-slate-600 hover:text-slate-200'}`}>
                                <input type="radio" name="inputType" value="url" checked={inputType === 'url'} onChange={() => handleInputTypeChange('url')} className="hidden" />
                                <i className="bi bi-link-45deg text-2xl mb-1"></i>
                                <span className="text-xs font-medium">Article URL</span>
                            </label>

                            <label className={`cursor-pointer border border-white/10 rounded-xl p-4 flex flex-col items-center justify-center transition-all ${inputType === 'pdf' ? 'bg-gradient-to-br from-violet-600 to-sky-500 text-white shadow-lg shadow-violet-500/40 border-transparent' : 'text-slate-400 hover:border-slate-600 hover:text-slate-200'}`}>
                                <input type="radio" name="inputType" value="pdf" checked={inputType === 'pdf'} onChange={() => handleInputTypeChange('pdf')} className="hidden" />
                                <i className="bi bi-file-earmark-pdf text-2xl mb-1"></i>
                                <span className="text-xs font-medium">PDF Document</span>
                            </label>
                        </div>
                    </div>

                    {/* Input Areas */}
                    <div className="mb-8 min-h-[150px]">
                        {inputType === 'text' && (
                            <div className="animate-[fadeIn_0.3s_ease-out]">
                                <label className="block text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Paste News Text</label>
                                <textarea
                                    className="w-full bg-white/5 border border-white/10 rounded-xl text-slate-100 p-4 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50 transition-all h-40 resize-none"
                                    placeholder="Paste the news article text here for deep analysis..."
                                    value={textInput}
                                    onChange={(e) => setTextInput(e.target.value)}
                                ></textarea>
                            </div>
                        )}

                        {inputType === 'url' && (
                            <div className="animate-[fadeIn_0.3s_ease-out]">
                                <label className="block text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Article Web Address</label>
                                <div className="flex bg-white/5 border border-white/10 rounded-xl overflow-hidden focus-within:border-violet-500 focus-within:ring-1 focus-within:ring-violet-500/50 transition-all">
                                    <span className="p-4 text-slate-400 bg-black/20 md:w-12 flex items-center justify-center"><i className="bi bi-browser-chrome"></i></span>
                                    <input
                                        type="url"
                                        className="w-full bg-transparent border-none text-slate-100 p-4 focus:outline-none"
                                        placeholder="https://example.com/news/article-abc"
                                        value={urlInput}
                                        onChange={(e) => setUrlInput(e.target.value)}
                                    />
                                </div>
                            </div>
                        )}

                        {inputType === 'pdf' && (
                            <div className="animate-[fadeIn_0.3s_ease-out]">
                                <label className="block text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">Drop PDF Document</label>
                                <div className="flex bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                                    <input
                                        type="file"
                                        id="fileUpload"
                                        accept=".pdf"
                                        className="w-full bg-transparent text-slate-400 file:mr-4 file:py-4 file:px-6 file:border-0 file:bg-white/10 file:text-slate-300 hover:file:bg-white/20 transition-all cursor-pointer"
                                        onChange={handleFileChange}
                                    />
                                    <button
                                        type="button"
                                        onClick={clearFile}
                                        className="px-6 text-red-400 hover:bg-red-500/10 hover:text-red-500 transition-colors border-l border-white/10"
                                    >
                                        <i className="bi bi-trash3-fill"></i>
                                    </button>
                                </div>
                                {fileName && <p className="mt-2 text-xs text-sky-400"><i className="bi bi-check-circle mr-1"></i> Selected: {fileName}</p>}
                            </div>
                        )}
                    </div>

                    {/* Submit Button */}
                    <div className="text-center pt-4">
                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-premium w-full md:w-auto md:min-w-[300px]"
                        >
                            {loading ? (
                                <span><span className="spinner-border spinner-border-sm mr-2 text-sm" role="status" aria-hidden="true"></span>Analyzing...</span>
                            ) : (
                                <span><span className="mr-2">Start Deep Analysis</span><i className="bi bi-stars"></i></span>
                            )}
                        </button>
                    </div>
                </form>
            )}

            {loading && (
                <div className="text-center my-12 animate-[fadeIn_0.5s_ease-out]">
                    {/* Particle effect could be added here similar to script.js but CSS animation of spinner is standard */}
                    <div className="inline-block w-12 h-12 border-4 border-violet-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                    <h5 className="font-bold text-xl mb-2">Orchestrating Agents...</h5>
                    <p className="text-slate-400 text-sm">Gathering context and running classifier...</p>
                </div>
            )}

            {error && (
                <div className="mt-8 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-200 flex items-center animate-[shakeX_0.5s]">
                    <i className="bi bi-exclamation-octagon-fill mr-3 text-red-500 text-xl"></i>
                    <span>Error: {error}</span>
                </div>
            )}

            {result && <ResultsParams result={result} onReset={() => setResult(null)} />}
        </div>
    );
};

export default AnalysisForm;
