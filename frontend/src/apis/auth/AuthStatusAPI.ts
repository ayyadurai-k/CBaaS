import { api } from '../configs/axiosConfig';
import { AxiosResponse } from 'axios';

export interface AuthStatusResponse {
  authenticated: boolean;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

export class AuthStatusAPI {
  static async getAuthStatus(): Promise<AxiosResponse<AuthStatusResponse>> {
    return await api.get<AuthStatusResponse>('/auth/status/');
  }
}
