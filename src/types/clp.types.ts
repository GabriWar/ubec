export interface Temperature {
  value: number;
  unit: string;
  sensor_type: string;
  address: string;
}

export interface Temperatures {
  ambiente: Temperature;
  quadro_eletrico: Temperature;
  modulo_fotovoltaico: Temperature;
  transformador: Temperature;
}

export interface Outputs {
  comunicacao_ok: boolean;
  usina_gerando: boolean;
  falha: boolean;
  alarme: boolean;
  emergencia_inversores: boolean;
  reset_rasp: boolean;
  reset_link_3g: boolean;
  reserva_1: boolean;
  reserva_2: boolean;
  reserva_3: boolean;
}

export interface Inputs {
  dj_geral_aberto: boolean;
  dj_geral_fechado: boolean;
  reserva_i02: boolean;
  reserva_i03: boolean;
  reserva_i04: boolean;
  reserva_i05: boolean;
  reserva_i06: boolean;
  reserva_i07: boolean;
  reserva_i08: boolean;
  reserva_i09: boolean;
  servico_auxiliar: boolean;
  botao_close: boolean;
  botao_trip: boolean;
  botao_emergencia: boolean;
}

export interface OperationalStatus {
  comunicacao_ok: boolean;
  sistema_ativo: boolean;
  em_falha: boolean;
  alarme_ativo: boolean;
  emergencia_ativa: boolean;
}

export interface ElectricalStatus {
  disjuntor_geral_status: 'FECHADO' | 'ABERTO';
  servico_auxiliar_ok: boolean;
}

export interface Status {
  outputs: Outputs;
  inputs: Inputs;
  operational: OperationalStatus;
  electrical: ElectricalStatus;
}

export interface Alert {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: string;
}

export interface Metadata {
  protocol: string;
  plc_model: string;
  firmware_version: string;
  data_quality: string;
}

export interface Location {
  site: string;
  installation: string;
}

export interface CLPData {
  device_id: string;
  timestamp: string;
  location: Location;
  sensors: {
    temperaturas: Temperatures;
  };
  status: Status;
  alerts: Alert[];
  metadata: Metadata;
}

export interface HistoricalData {
  timestamp: string;
  temperature: number;
  sensor: string;
}
