// src/apis/auth/SignupAPI.ts
import { api } from "../configs/axiosConfig";
import { AxiosResponse } from "axios";

export type SignupPayload = {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  organization_name?: string;
};

export type SignupResponse = {
  message: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
  };
};

export const SignupAPI = {
  signup: (payload: SignupPayload): Promise<AxiosResponse<SignupResponse>> => 
    api.post<SignupResponse>("/auth/signup/", payload),
};
