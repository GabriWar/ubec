import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import type { CLPData } from '../types/clp.types';
import { sseService } from '../services/sse.service';
import { apiService } from '../services/api.service';

interface CLPContextType {
  data: CLPData | null;
  isConnected: boolean;
  lastUpdate: string | null;
  error: string | null;
}

const CLPContext = createContext<CLPContextType | undefined>(undefined);

export function CLPProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<CLPData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Buscar dados iniciais via HTTP (opcional - não bloqueia se não houver dados)
    apiService
      .getCurrentData()
      .then((initialData) => {
        setData(initialData);
        setLastUpdate(initialData.timestamp);
      })
      .catch(() => {
        // Silencioso - aguardar dados via SSE
        console.log('Aguardando dados do CLP...');
      });

    // Conectar SSE
    sseService.connect();

    // Handlers
    const unsubscribeMessage = sseService.onMessage((newData) => {
      setData(newData);
      setLastUpdate(newData.timestamp);
      setError(null);
    });

    const unsubscribeConnect = sseService.onConnect(() => {
      setIsConnected(true);
      setError(null);
    });

    const unsubscribeDisconnect = sseService.onDisconnect(() => {
      setIsConnected(false);
    });

    const unsubscribeError = sseService.onError(() => {
      setError('Erro de conexão com o servidor');
    });

    // Cleanup
    return () => {
      unsubscribeMessage();
      unsubscribeConnect();
      unsubscribeDisconnect();
      unsubscribeError();
      sseService.disconnect();
    };
  }, []);

  return (
    <CLPContext.Provider value={{ data, isConnected, lastUpdate, error }}>
      {children}
    </CLPContext.Provider>
  );
}

export function useCLP() {
  const context = useContext(CLPContext);
  if (context === undefined) {
    throw new Error('useCLP deve ser usado dentro de um CLPProvider');
  }
  return context;
}
