// src/apis/auth/SignupAPI.ts
import { api } from "../configs/axiosConfig";
import { AxiosResponse } from "axios";

export type SignupPayload = {
  email: string;
  password: string;
  confirm_password: string;
  name: string;
  phone_number?: string;
  organization_name?: string;
};

export type SignupResponse = {
  access: string;
  refresh: string;
};

export const SignupAPI = {
  signup: (payload: SignupPayload): Promise<AxiosResponse<SignupResponse>> => 
    api.post<SignupResponse>("/auth/signup/", payload),
};
