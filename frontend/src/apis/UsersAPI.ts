// src/apis/users/UsersAPI.ts
import { api } from "../../lib/api";
import { AxiosResponse } from "axios";

export type UserDTO = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  is_active: boolean;
  date_joined: string;
};

export type UpdateProfilePayload = {
  first_name?: string;
  last_name?: string;
  phone_number?: string;
};

export const UsersAPI = {
  getProfile: (): Promise<AxiosResponse<UserDTO>> => 
    api.get<UserDTO>("/user/profile/"),
  
  updateProfile: (payload: UpdateProfilePayload): Promise<AxiosResponse<UserDTO>> => 
    api.put<UserDTO>("/user/profile/", payload),
};
