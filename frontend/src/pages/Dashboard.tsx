import { useEffect, useState } from 'react';
import { ThemeProvider, ThemeToggle } from '../components/ThemeProvider';
import { VideoFeed } from '../components/VideoFeed';
import { SafetyPanel } from '../components/SafetyPanel';
import { FiMonitor } from 'react-icons/fi';
import { createWebSocketConnection, getVideoStreamUrl } from '../services/api';
import type { DashboardData } from '../types';

interface ExtendedDashboardData extends DashboardData {
    travas?: number;
}

export const Dashboard = () => {
  const [data, setData] = useState<ExtendedDashboardData>({
    status: "CONECTANDO...",
    mensagem: "Iniciando sistema...",
    perigo: false,
    panelas: 0,
    garras: 0,
    travas: 0
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
            mensagem: parsed.mensagem,
            perigo: parsed.perigo,
            panelas: parsed.panelas || 0,
            garras: parsed.garras || 0,
            travas: parsed.travas || 0
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

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors duration-300 font-sans flex flex-col">
        
        <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between sticky top-0 z-20 shadow-sm">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-600 rounded-lg shadow-md text-white">
                    <FiMonitor className="w-5 h-5" />
                </div>
                <div>
                    <h1 className="text-lg font-bold text-gray-900 dark:text-white leading-tight">
                        Monitoramento de trava <span className="text-blue-500">da panela </span>
                    </h1>
                </div>
            </div>
            <ThemeToggle />
        </header>

        <main className="flex-grow p-4 lg:p-6 max-w-[1920px] mx-auto w-full">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full min-h-[500px]">
                
                <div className="lg:col-span-8 flex flex-col">
                    <div className="bg-black rounded-2xl overflow-hidden shadow-2xl border border-gray-700 flex-grow relative">
                        <VideoFeed 
                            streamUrl={videoUrl}
                            isDanger={data.perigo}
                            isOnline={isOnline}
                        />
                    </div>
                </div>

                <div className="lg:col-span-4 flex flex-col h-full">
                    <SafetyPanel 
                        status={data.status}
                        isSafe={!data.perigo}
                    />
                </div>
            </div>
        </main>
      </div>
    </ThemeProvider>
  );
};

export default Dashboard;
