// src/apis/OpsAPI.ts
import { api } from "./configs/axiosConfig";
import { AxiosResponse } from "axios";

export type HealthStatus = {
  status: "healthy" | "unhealthy";
  checks: {
    database: boolean;
    redis?: boolean;
    storage?: boolean;
  };
  timestamp: string;
};

export type ReadinessStatus = {
  status: "ready" | "not_ready";
  checks: {
    database: boolean;
    migrations: boolean;
    dependencies: boolean;
  };
  timestamp: string;
};

export const OpsAPI = {
  healthCheck: (): Promise<AxiosResponse<HealthStatus>> => 
    api.get<HealthStatus>("/healthz/"),
  
  readinessCheck: (): Promise<AxiosResponse<ReadinessStatus>> => 
    api.get<ReadinessStatus>("/readyz/"),
};
