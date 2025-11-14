import type { CLPData } from '../types/clp.types';

type MessageHandler = (data: CLPData) => void;
type ConnectionHandler = () => void;
type ErrorHandler = (error: Event) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval: number = 5000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private disconnectionHandlers: Set<ConnectionHandler> = new Set();
  private errorHandlers: Set<ErrorHandler> = new Set();

  constructor(url: string = 'ws://localhost:3001') {
    this.url = url;
  }

  connect(): void {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket conectado');
        this.clearReconnectTimer();
        this.connectionHandlers.forEach(handler => handler());
      };

      this.ws.onmessage = (event) => {
        try {
          const data: CLPData = JSON.parse(event.data);
          this.messageHandlers.forEach(handler => handler(data));
        } catch (error) {
          console.error('Erro ao parsear mensagem WebSocket:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('Erro no WebSocket:', error);
        this.errorHandlers.forEach(handler => handler(error));
      };

      this.ws.onclose = () => {
        console.log('WebSocket desconectado');
        this.disconnectionHandlers.forEach(handler => handler());
        this.scheduleReconnect();
      };
    } catch (error) {
      console.error('Erro ao conectar WebSocket:', error);
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    this.clearReconnectTimer();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket não está conectado');
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
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export const websocketService = new WebSocketService(
  import.meta.env.VITE_WS_URL || 'ws://localhost:3001'
);
