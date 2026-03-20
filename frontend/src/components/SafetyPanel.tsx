import React from 'react';
import { FiActivity, FiLock, FiUnlock } from 'react-icons/fi';

interface SafetyPanelProps {
  status: string;
  isSafe: boolean;
}

export const SafetyPanel: React.FC<SafetyPanelProps> = ({ status, isSafe }) => {
  
  const getStatusConfig = () => {
    if (status.includes("DESTRAVADO") || (!isSafe && status !== "MONITORANDO" && status !== "CONECTANDO...")) {
      return {
        containerClasses: 'bg-red-600 dark:bg-red-700 border-red-500',
        textClasses: 'text-white',
        subTextClasses: 'text-red-100 bg-red-900/30',
        icon: <FiUnlock className="w-24 h-24 mb-4 animate-bounce text-white" />,
        title: "PERIGO: DESTRAVADO",
        subtext: "PARE A OPERAÇÃO IMEDIATAMENTE",
        animation: "animate-pulse"
      };
    }
    
    if (status.includes("SEGURO") || status.includes("TRAVADO")) {
      return {
        containerClasses: 'bg-green-600 dark:bg-green-700 border-green-500',
        textClasses: 'text-white',
        subTextClasses: 'text-green-100 bg-green-900/30',
        icon: <FiLock className="w-24 h-24 mb-4 text-white" />,
        title: "OPERAÇÃO SEGURA",
        subtext: "Ganchos Acoplados e Travados",
        animation: ""
      };
    }

    return {
      containerClasses: 'bg-gray-50 border-gray-200 dark:bg-background-secondary dark:border-background-tertiary',
      textClasses: 'text-gray-600 dark:text-gray-300',
      subTextClasses: 'text-gray-500 dark:text-gray-400 bg-gray-200/50 dark:bg-black/20',
      icon: <FiActivity className="w-24 h-24 mb-4 text-blue-500 dark:text-blue-400" />,
      title: status || "MONITORANDO",
      subtext: "Aguardando detecção na área...",
      animation: ""
    };
  };

  const config = getStatusConfig();

  return (
    <div className={`h-full rounded-2xl border-4 shadow-xl overflow-hidden flex flex-col justify-center items-center text-center p-8 transition-all duration-500 ${config.containerClasses} ${config.animation}`}>
      
      <div className="drop-shadow-md">
        {config.icon}
      </div>

      <h2 className={`text-3xl md:text-5xl font-black uppercase tracking-wider mb-6 drop-shadow-sm ${config.textClasses}`}>
        {config.title}
      </h2>

      <p className={`text-lg md:text-xl font-medium px-6 py-2 rounded-full backdrop-blur-sm ${config.subTextClasses}`}>
        {config.subtext}
      </p>

    </div>
  );
};
