// src/services/UsersService.ts
import { UsersAPI, UserDTO, UpdateProfilePayload, OrganizationDTO } from "../apis/UsersAPI";

export type User = {
  id: string;
  email: string;
  name: string;
  role: string;
  phone_number?: string;
  created_at: string;
  updated_at: string;
  organization: OrganizationDTO | null;
  profile_picture_url?: string | null;
  // Additional computed fields for backwards compatibility
  is_active: boolean;
  date_joined: string;
  full_name: string;
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
      ...user, // Include all UserDTO properties (id, email, name, role, phone_number, created_at, updated_at, organization, profile_picture_url)
      is_active: true, // Default value since UserDTO doesn't have this field
      date_joined: user.created_at, // Map created_at to date_joined (keep as string for Redux serialization)
      full_name: user.name, // Map name to full_name
    };
  }
}

// Singleton instance for app-wide usage
export const usersService = new UsersService();
