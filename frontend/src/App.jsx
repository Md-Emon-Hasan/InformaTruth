import React from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import AnalysisForm from './components/AnalysisForm';
import Footer from './components/Footer';

function App() {
  return (
    <div className="flex flex-col min-h-screen relative overflow-hidden">
      {/* Background Blobs */}
      <div className="blob w-[500px] h-[500px] bg-violet-600 top-[-10%] left-[-10%]"></div>
      <div className="blob w-[600px] h-[600px] bg-sky-500 bottom-[-20%] right-[-10%] animation-delay-[-5s]" style={{ animationDelay: '-5s' }}></div>

      <Navbar />

      <main className="container mx-auto px-4 py-12 flex-grow flex flex-col items-center justify-center">
        <div className="w-full max-w-4xl">
          <Hero />
          <AnalysisForm />
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default App;
