// src/services/OrganizationsService.ts
import { OrganizationsAPI, OrganizationDTO, UpdateOrganizationPayload } from "../apis/OrganizationsAPI";

export type Organization = {
  id: string;
  name: string;
  slug: string;
  logo_url?: string | null;
  created_at: Date;
  updated_at: Date;
};

export class OrganizationsService {
  async getUserOrganization(): Promise<Organization> {
    const { data } = await OrganizationsAPI.getUserOrganization();
    return this.normalizeOrganization(data);
  }

  async updateUserOrganization(payload: UpdateOrganizationPayload): Promise<Organization> {
    const { data } = await OrganizationsAPI.updateUserOrganization(payload);
    return this.normalizeOrganization(data);
  }

  async uploadOrganizationLogo(file: File): Promise<Organization> {
    const { data } = await OrganizationsAPI.uploadOrganizationLogo(file);
    return this.normalizeOrganization(data);
  }

  async deleteOrganizationLogo(): Promise<Organization> {
    const { data } = await OrganizationsAPI.deleteOrganizationLogo();
    return this.normalizeOrganization(data);
  }

  async deleteOrganization(): Promise<void> {
    await OrganizationsAPI.deleteOrganization();
  }

  private normalizeOrganization(org: OrganizationDTO): Organization {
    return {
      ...org,
      created_at: new Date(org.created_at),
      updated_at: new Date(org.updated_at),
    };
  }
}

// Singleton instance for app-wide usage
export const organizationsService = new OrganizationsService();
