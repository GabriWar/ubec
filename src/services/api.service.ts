import type { CLPData, HistoricalData } from '../types/clp.types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

class APIService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  async getCurrentData(): Promise<CLPData> {
    return this.request<CLPData>('/clp/current');
  }

  async getHistoricalData(
    sensor: string,
    startTime: string,
    endTime: string
  ): Promise<HistoricalData[]> {
    const params = new URLSearchParams({
      sensor,
      start: startTime,
      end: endTime,
    });
    return this.request<HistoricalData[]>(`/clp/history?${params}`);
  }

  async getAlerts(): Promise<CLPData['alerts']> {
    return this.request<CLPData['alerts']>('/clp/alerts');
  }

  async getStatus(): Promise<{ connected: boolean; lastUpdate: string }> {
    return this.request<{ connected: boolean; lastUpdate: string }>('/clp/status');
  }
}

export const apiService = new APIService();
