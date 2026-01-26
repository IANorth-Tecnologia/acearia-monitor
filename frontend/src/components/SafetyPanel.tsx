import React from 'react';
import { FiActivity, FiLock, FiUnlock } from 'react-icons/fi';

interface SafetyPanelProps {
  status: string;
  isSafe: boolean;
}

export const SafetyPanel: React.FC<SafetyPanelProps> = ({ status, isSafe }) => {
  
  const getStatusConfig = () => {
    if (!isSafe) {
      return {
        bgColor: 'bg-red-600',
        borderColor: 'border-red-400',
        textColor: 'text-white',
        icon: <FiUnlock className="w-24 h-24 mb-4 animate-bounce" />, 
        title: "PERIGO: DESTRAVADO",
        subtext: "PARE A OPERAÇÃO IMEDIATAMENTE",
        animation: "animate-pulse" 
      };
    }
    
    if (status.includes("SEGURO") || status.includes("TRAVADO")) {
      return {
        bgColor: 'bg-green-600',
        borderColor: 'border-green-400',
        textColor: 'text-white',
        icon: <FiLock className="w-24 h-24 mb-4" />, 
        title: "OPERAÇÃO SEGURA",
        subtext: "Ganchos Acoplados e Travados",
        animation: ""
      };
    }

    return {
      bgColor: 'bg-gray-800',
      borderColor: 'border-gray-600',
      textColor: 'text-gray-300',
      icon: <FiActivity className="w-24 h-24 mb-4 text-blue-400" />,
      title: status || "MONITORANDO",
      subtext: "Aguardando detecção...",
      animation: ""
    };
  };

  const config = getStatusConfig();

  return (
    <div className={`h-full rounded-2xl border-4 shadow-2xl overflow-hidden flex flex-col justify-center items-center text-center p-8 transition-all duration-500 ${config.bgColor} ${config.borderColor} ${config.animation}`}>
      
      <div className="text-white drop-shadow-lg">
        {config.icon}
      </div>

      <h2 className={`text-4xl md:text-5xl font-black uppercase tracking-wider mb-4 drop-shadow-md text-white`}>
        {config.title}
      </h2>

      <p className="text-lg md:text-xl font-medium text-white/90 bg-black/20 px-6 py-2 rounded-full backdrop-blur-sm">
        {config.subtext}
      </p>

    </div>
  );
};
