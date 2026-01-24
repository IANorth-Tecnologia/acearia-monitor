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
    mensagem: "Iniciando sistema...",
    perigo: false,
    panelas: 0,
    garras: 0
  });

  const videoUrl = getVideoStreamUrl();

  useEffect(() => {
    const ws = createWebSocketConnection();
    
    ws.onmessage = (event) => {
      try {
        const parsed: DashboardData = JSON.parse(event.data);
        setData(parsed);
      } catch (e) {
        console.error("Erro no WS:", e);
      }
    };

    return () => {
        if(ws.readyState === 1) ws.close();
    };
  }, []);

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-gray-50 dark:bg-background-primary transition-colors duration-300 font-sans">
        <header className="bg-white dark:bg-background-secondary border-b border-gray-200 dark:border-background-tertiary px-6 py-4 flex items-center justify-between sticky top-0 z-20 shadow-sm">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-accent-primary to-blue-600 rounded-lg shadow-lg text-white">
                    <FiMonitor className="w-6 h-6" />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-gray-900 dark:text-text-primary leading-tight">
                        Acearia <span className="text-accent-primary">Monitor</span>
                    </h1>
                    <p className="text-xs text-gray-500 dark:text-text-tertiary">Detecção de Riscos em Panelas</p>
                </div>
            </div>
            <ThemeToggle />
        </header>

        <main className="p-4 sm:p-6 lg:p-8 max-w-[1920px] mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                <div className="lg:col-span-3 space-y-4">
                    <div className="bg-white dark:bg-background-secondary p-1 rounded-xl border border-gray-200 dark:border-background-tertiary shadow-sm">
                        <VideoFeed 
                            streamUrl={videoUrl}
                            isDanger={data.perigo}
                        />
                    </div>
                </div>

                <div className="lg:col-span-2">
                    <SafetyPanel 
                        status={data.status}
                        isDanger={data.perigo}
                        stats={{ panelas: data.panelas, garras: data.garras }}
                    />
                </div>
            </div>
        </main>
      </div>
    </ThemeProvider>
  );
};
