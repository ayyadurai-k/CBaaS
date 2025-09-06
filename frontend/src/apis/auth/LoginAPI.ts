// src/apis/auth/LoginAPI.ts
import { api } from "../configs/axiosConfig";
import { AxiosResponse } from "axios";

export type LoginPayload = {
  email: string;
  password: string;
};

export type LoginResponse = {
  access: string;
  refresh: string;
  user: {
    id: string;
    email: string;
    name: string;
  };
};

export type TokenRefreshPayload = {
  refresh: string;
};

export type TokenRefreshResponse = {
  access: string;
};

export const LoginAPI = {
  login: (payload: LoginPayload): Promise<AxiosResponse<LoginResponse>> => 
    api.post<LoginResponse>("/auth/login/", payload),
  
  refreshToken: (payload: TokenRefreshPayload): Promise<AxiosResponse<TokenRefreshResponse>> => 
    api.post<TokenRefreshResponse>("/auth/token/refresh/", payload),
};
