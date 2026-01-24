import React from 'react';
import { FiAlertTriangle, FiCheckCircle, FiBox, FiAnchor, FiActivity } from 'react-icons/fi';
import type { SafetyStats } from '../types';

interface SafetyPanelProps {
  status: string;
  isDanger: boolean;
  stats: SafetyStats;
}

const InfoCard: React.FC<{ icon: React.ReactNode; label: string; value: string | number; colorClass?: string }> = ({ icon, label, value, colorClass = "text-accent-primary" }) => (
  <div className="bg-white dark:bg-background-secondary p-4 rounded-lg flex items-center border border-gray-200 dark:border-background-tertiary shadow-sm transition-colors duration-300">
    <div className={`mr-4 text-3xl ${colorClass}`}>
      {icon}
    </div>
    <div>
      <p className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-text-tertiary">{label}</p>
      <p className="text-2xl font-bold text-gray-900 dark:text-text-primary">{value}</p>
    </div>
  </div>
);

export const SafetyPanel: React.FC<SafetyPanelProps> = ({ status, isDanger, stats }) => {
  const statusConfig = isDanger 
    ? { color: 'text-status-danger', border: 'border-status-danger', icon: <FiAlertTriangle className="w-8 h-8" /> }
    : { color: 'text-status-success', border: 'border-status-success', icon: <FiCheckCircle className="w-8 h-8" /> };

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className={`p-6 rounded-lg border-l-8 shadow-md transition-all duration-300 bg-white dark:bg-background-secondary ${statusConfig.border}`}>
        <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-bold uppercase tracking-widest text-gray-500 dark:text-text-secondary">Status Operacional</h2>
            <div className={`animate-pulse ${statusConfig.color}`}>{statusConfig.icon}</div>
        </div>
        <p className={`text-4xl font-black ${statusConfig.color} tracking-tight`}>
            {status}
        </p>
        <p className="text-sm mt-3 text-gray-600 dark:text-text-tertiary">
            {isDanger ? "INTERVENÇÃO IMEDIATA NECESSÁRIA" : "Monitoramento ativo e seguro."}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <InfoCard icon={<FiBox />} label="Panelas" value={stats.panelas} colorClass="text-blue-500"/>
        <InfoCard icon={<FiAnchor />} label="Garras" value={stats.garras} colorClass="text-yellow-500"/>
      </div>

      <div className="bg-white dark:bg-background-secondary p-4 rounded-lg border border-gray-200 dark:border-background-tertiary flex-grow shadow-sm">
        <div className="flex items-center gap-2 mb-4 border-b border-gray-100 dark:border-background-tertiary pb-2">
            <FiActivity className="text-gray-400" />
            <span className="font-semibold text-gray-700 dark:text-text-secondary">Atividade Recente</span>
        </div>
        <div className="space-y-2 text-xs text-gray-500 dark:text-text-tertiary font-mono">
            <p>Sistema Acearia Monitor iniciado...</p>
            {isDanger && <p className="text-status-danger font-bold">ALERTA DE SEGURANÇA REGISTRADO</p>}
        </div>
      </div>
    </div>
  );
};
