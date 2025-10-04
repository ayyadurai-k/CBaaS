// src/apis/auth/LogoutAPI.ts
import { api } from "../configs/axiosConfig";
import { AxiosResponse } from "axios";

export type LogoutPayload = {
  refresh: string;
};

export type LogoutResponse = {
  detail: string;
};

export const LogoutAPI = {
  logout: (payload: LogoutPayload): Promise<AxiosResponse<LogoutResponse>> => 
    api.post<LogoutResponse>("/auth/logout/", payload),
};
