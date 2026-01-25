import React from 'react';
import { FiVideoOff } from 'react-icons/fi';

interface VideoFeedProps {
  streamUrl?: string;
  isDanger: boolean;
  isOnline: boolean;
}

export const VideoFeed: React.FC<VideoFeedProps> = ({ streamUrl, isDanger, isOnline }) => {
  return (
    <div className={`relative w-full aspect-video bg-black dark:bg-background-tertiary rounded-lg overflow-hidden shadow-lg border-4 transition-all duration-300 ${isDanger ? 'border-status-danger shadow-red-900/20' : 'border-gray-200 dark:border-background-tertiary'}`}>
      {streamUrl ? (
        <img
          src={streamUrl}
          alt="Monitoramento Acearia"
          className="w-full h-full object-contain"
          onError={(e) => { e.currentTarget.style.display = 'none'; }}
        />
      ) : (
        <div className="flex flex-col items-center justify-center h-full text-text-tertiary">
          <FiVideoOff size={48} className="mb-4 opacity-50" />
          <p className="font-semibold">Aguardando sinal de vídeo...</p>
        </div>
      )}

      <div className="absolute top-4 right-4 flex items-center gap-2 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full border border-white/10 shadow-lg">
        <div className={`w-2 h-2 rounded-full ${isDanger ? 'bg-status-danger animate-pulse' : 'bg-status-success'}`}></div>
        <span className="text-[10px] font-bold text-white tracking-widest">
            {isOnline ? 'LIVE' : 'SINAL PERDIDO'}
        </span>
      </div>

      {isDanger && (
        <div className="absolute inset-0 border-[6px] border-status-danger/50 animate-pulse pointer-events-none"></div>
      )}
    </div>
  );
};
