// src/apis/auth/LogoutAPI.ts
import { api } from "../configs/axiosConfig";
import { AxiosResponse } from "axios";

export type LogoutResponse = {
  message: string;
};

export const LogoutAPI = {
  logout: (): Promise<AxiosResponse<LogoutResponse>> => 
    api.post<LogoutResponse>("/auth/logout/", {}),
};
