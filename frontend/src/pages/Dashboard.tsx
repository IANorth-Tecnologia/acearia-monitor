import { useEffect, useState } from 'react';
import { ThemeProvider, ThemeToggle } from '../components/ThemeProvider';
import { VideoFeed } from '../components/VideoFeed';
import { SafetyPanel } from '../components/SafetyPanel';
import { FiMonitor } from 'react-icons/fi';
import { createWebSocketConnection, getVideoStreamUrl } from '../services/api';
import type { DashboardData } from '../types';

export const Dashboard = () => {
  const [data, setData] = useState<DashboardData>({
    status: "CONECTANDO...",
    perigo: false,
  });

  const [isOnline, setIsOnline] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  const videoUrl = getVideoStreamUrl();

  useEffect(() => {
    const ws = createWebSocketConnection();

    ws.onopen = () => console.log("WebSocket CONECTADO! ✅");
    
    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        setLastUpdate(Date.now());
        setIsOnline(true);
        
        setData({
            status: parsed.status,
            perigo: parsed.perigo
        });
      } catch (e) {
        console.error("Erro no WS:", e);
      }
    };

    const checker = setInterval(() => {
        if (Date.now() - lastUpdate > 3000) setIsOnline(false);
    }, 2000);

    return () => {
        if(ws.readyState === 1) ws.close();
        clearInterval(checker);
    };
  }, [lastUpdate]);

  const getScreenAura = () => {
    if (!isOnline) return "bg-gray-100 dark:bg-gray-900"; // Neutro

    if (data.perigo || data.status.includes("DESTRAVADO")) {
      return "bg-red-50 dark:bg-red-950/40 shadow-[inset_0_0_120px_rgba(220,38,38,0.4)] animate-pulse transition-colors duration-700";
    }
    
    if (data.status.includes("TRAVADO") || data.status.includes("SEGURO")) {
      return "bg-green-50 dark:bg-green-950/30 shadow-[inset_0_0_120px_rgba(22,163,74,0.3)] transition-colors duration-700";
    }

    return "bg-gray-100 dark:bg-gray-900 transition-colors duration-700";
  };

  return (
    <ThemeProvider>
      <div className={`min-h-screen font-sans flex flex-col ${getScreenAura()}`}>
        
        <header className="bg-white/80 dark:bg-black/40 backdrop-blur-md border-b border-gray-200/50 dark:border-gray-800/50 px-6 py-4 flex items-center justify-between sticky top-0 z-20 shadow-sm transition-colors duration-300">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-600 rounded-lg shadow-lg text-white">
                    <FiMonitor className="w-6 h-6" />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-gray-900 dark:text-white leading-tight drop-shadow-sm">
                        Acearia <span className="text-blue-500">Monitor</span>
                    </h1>
                    <p className="text-xs text-gray-600 dark:text-gray-400 font-medium">Detecção de Riscos em Panelas</p>
                </div>
            </div>
            <ThemeToggle />
        </header>

        <main className="flex-grow p-4 lg:p-6 max-w-[1920px] mx-auto w-full z-10 relative">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full min-h-[600px]">
                
                <div className="lg:col-span-8 flex flex-col">
                    <div className={`bg-black rounded-2xl overflow-hidden shadow-2xl border-4 flex-grow relative transition-colors duration-500 ${data.perigo && isOnline ? 'border-red-600' : 'border-gray-700'}`}>
                        <VideoFeed 
                            streamUrl={videoUrl}
                            isDanger={data.perigo}
                            isOnline={isOnline}
                        />
                    </div>
                </div>

                <div className="lg:col-span-4 flex flex-col h-full">
                    <SafetyPanel 
                        status={isOnline ? data.status : "SINAL PERDIDO"}
                        isSafe={!data.perigo && isOnline}
                    />
                </div>
            </div>
        </main>
      </div>
    </ThemeProvider>
  );
};

export default Dashboard;
