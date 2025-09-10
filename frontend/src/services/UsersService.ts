// src/services/UsersService.ts
import { UsersAPI, UserDTO, UpdateProfilePayload } from "../apis/UsersAPI";

export type User = {
  id: string;
  email: string;
  name: string;
  phone_number?: string;
  is_active: boolean;
  date_joined: Date;
  full_name: string;
  profile_picture_url?: string | null;
};

export class UsersService {
  async getProfile(): Promise<User> {
    const { data } = await UsersAPI.getProfile();
    return this.normalizeUser(data);
  }

  async updateProfile(payload: UpdateProfilePayload): Promise<User> {
    const { data } = await UsersAPI.updateProfile(payload);
    return this.normalizeUser(data);
  }

  private normalizeUser(user: UserDTO): User {
    return {
      ...user,
      is_active: true, // Default value since UserDTO doesn't have this field
      date_joined: new Date(user.created_at), // Map created_at to date_joined
      full_name: user.name,
    };
  }
}

// Singleton instance for app-wide usage
export const usersService = new UsersService();
