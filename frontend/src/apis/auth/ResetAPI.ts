// src/apis/auth/ResetAPI.ts
import { api } from "../configs/axiosConfig";
import { AxiosResponse } from "axios";

export type ForgotPasswordPayload = {
  email: string;
};

export type ForgotPasswordResponse = {
  message: string;
};

export type VerifyResetTokenPayload = {
  token: string;
};

export type VerifyResetTokenResponse = {
  valid: boolean;
  message: string;
};

export type ResetPasswordPayload = {
  token: string;
  new_password: string;
};

export type ResetPasswordResponse = {
  message: string;
};

export const ResetAPI = {
  forgotPassword: (payload: ForgotPasswordPayload): Promise<AxiosResponse<ForgotPasswordResponse>> => 
    api.post<ForgotPasswordResponse>("/auth/forgot-password/", payload),
  
  verifyResetToken: (payload: VerifyResetTokenPayload): Promise<AxiosResponse<VerifyResetTokenResponse>> => 
    api.post<VerifyResetTokenResponse>("/auth/verify-reset-token/", payload),
  
  resetPassword: (payload: ResetPasswordPayload): Promise<AxiosResponse<ResetPasswordResponse>> => 
    api.post<ResetPasswordResponse>("/auth/reset-password/", payload),
};
