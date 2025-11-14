import type { CLPData } from '../types/clp.types';

type MessageHandler = (data: CLPData) => void;
type ErrorHandler = (error: Event) => void;
type ConnectionHandler = () => void;

class SSEService {
  private eventSource: EventSource | null = null;
  private url: string;
  private reconnectInterval: number = 5000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private disconnectionHandlers: Set<ConnectionHandler> = new Set();
  private errorHandlers: Set<ErrorHandler> = new Set();

  constructor(url: string = 'http://localhost:3001/api/clp/stream') {
    this.url = url;
  }

  connect(): void {
    try {
      this.eventSource = new EventSource(this.url);

      this.eventSource.onopen = () => {
        console.log('SSE conectado');
        this.clearReconnectTimer();
        this.connectionHandlers.forEach(handler => handler());
      };

      this.eventSource.onmessage = (event) => {
        try {
          const data: CLPData = JSON.parse(event.data);
          this.messageHandlers.forEach(handler => handler(data));
        } catch (error) {
          console.error('Erro ao parsear mensagem SSE:', error);
        }
      };

      this.eventSource.onerror = (error) => {
        console.error('Erro no SSE:', error);
        this.errorHandlers.forEach(handler => handler(error));
        this.disconnect();
        this.scheduleReconnect();
      };

    } catch (error) {
      console.error('Erro ao conectar SSE:', error);
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    this.clearReconnectTimer();
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      this.disconnectionHandlers.forEach(handler => handler());
    }
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onConnect(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    return () => this.connectionHandlers.delete(handler);
  }

  onDisconnect(handler: ConnectionHandler): () => void {
    this.disconnectionHandlers.add(handler);
    return () => this.disconnectionHandlers.delete(handler);
  }

  onError(handler: ErrorHandler): () => void {
    this.errorHandlers.add(handler);
    return () => this.errorHandlers.delete(handler);
  }

  private scheduleReconnect(): void {
    if (!this.reconnectTimer) {
      console.log(`Tentando reconectar em ${this.reconnectInterval / 1000}s...`);
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, this.reconnectInterval);
    }
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  isConnected(): boolean {
    return this.eventSource !== null && this.eventSource.readyState === EventSource.OPEN;
  }
}

export const sseService = new SSEService(
  import.meta.env.VITE_SSE_URL || 'http://localhost:3001/api/clp/stream'
);
