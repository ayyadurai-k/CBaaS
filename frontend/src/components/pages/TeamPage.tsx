
import React, { useState } from 'react';
import { UserPlus, Users, Mail, Shield, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'Owner' | 'Admin' | 'Developer' | 'Viewer';
  status: 'Active' | 'Pending' | 'Inactive';
  joinDate: string;
}

const mockTeamMembers: TeamMember[] = [
  {
    id: '1',
    name: 'John Doe',
    email: 'john@acmecorp.com',
    role: 'Owner',
    status: 'Active',
    joinDate: '2024-01-01'
  },
  {
    id: '2',
    name: 'Jane Smith',
    email: 'jane@acmecorp.com',
    role: 'Admin',
    status: 'Active',
    joinDate: '2024-01-05'
  },
  {
    id: '3',
    name: 'Mike Johnson',
    email: 'mike@acmecorp.com',
    role: 'Developer',
    status: 'Pending',
    joinDate: '2024-01-15'
  }
];

export const TeamPage: React.FC = () => {
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>(mockTeamMembers);

  const getRoleColor = (role: TeamMember['role']) => {
    switch (role) {
      case 'Owner':
        return 'bg-purple-100 text-purple-800';
      case 'Admin':
        return 'bg-blue-100 text-blue-800';
      case 'Developer':
        return 'bg-green-100 text-green-800';
      case 'Viewer':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: TeamMember['status']) => {
    switch (status) {
      case 'Active':
        return 'bg-green-100 text-green-800';
      case 'Pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'Inactive':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const removeMember = (memberId: string) => {
    setTeamMembers(teamMembers.filter(member => member.id !== memberId));
  };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
      <div className="desktop-flex-between" style={{ marginBottom: '32px' }}>
        <div>
          <h1 
            className="font-bold text-slate-900"
            style={{ fontSize: '30px', lineHeight: '36px', marginBottom: '8px' }}
          >
            Team & Roles
          </h1>
          <p 
            className="text-slate-600"
            style={{ fontSize: '16px' }}
          >
            Manage team members and their access permissions
          </p>
        </div>
        <Button 
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium"
          style={{ padding: '12px 24px' }}
        >
          <UserPlus style={{ width: '20px', height: '20px', marginRight: '8px' }} />
          Invite Member
        </Button>
      </div>

      {teamMembers.length > 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div style={{ overflowX: 'auto', minWidth: '800px' }}>
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th 
                    className="text-left font-semibold text-slate-900"
                    style={{ padding: '16px 24px', fontSize: '14px' }}
                  >
                    Member
                  </th>
                  <th 
                    className="text-left font-semibold text-slate-900"
                    style={{ padding: '16px 24px', fontSize: '14px' }}
                  >
                    Email
                  </th>
                  <th 
                    className="text-left font-semibold text-slate-900"
                    style={{ padding: '16px 24px', fontSize: '14px' }}
                  >
                    Role
                  </th>
                  <th 
                    className="text-left font-semibold text-slate-900"
                    style={{ padding: '16px 24px', fontSize: '14px' }}
                  >
                    Status
                  </th>
                  <th 
                    className="text-left font-semibold text-slate-900"
                    style={{ padding: '16px 24px', fontSize: '14px' }}
                  >
                    Joined
                  </th>
                  <th 
                    className="text-left font-semibold text-slate-900"
                    style={{ padding: '16px 24px', fontSize: '14px' }}
                  >
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {teamMembers.map((member) => (
                  <tr key={member.id} className="hover:bg-slate-50 transition-colors">
                    <td style={{ padding: '16px 24px' }}>
                      <div className="flex items-center" style={{ gap: '12px' }}>
                        <div 
                          className="bg-blue-600 rounded-full flex items-center justify-center"
                          style={{ width: '40px', height: '40px' }}
                        >
                          <span 
                            className="text-white font-medium"
                            style={{ fontSize: '14px' }}
                          >
                            {member.name.split(' ').map(n => n[0]).join('')}
                          </span>
                        </div>
                        <span 
                          className="font-medium text-slate-900"
                          style={{ fontSize: '14px' }}
                        >
                          {member.name}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <div className="flex items-center" style={{ gap: '8px' }}>
                        <Mail className="text-slate-500" style={{ width: '16px', height: '16px' }} />
                        <span 
                          className="text-slate-600"
                          style={{ fontSize: '14px' }}
                        >
                          {member.email}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <span 
                        className={`inline-flex items-center rounded-full font-medium ${getRoleColor(member.role)}`}
                        style={{ 
                          padding: '4px 10px',
                          fontSize: '12px',
                          gap: '4px'
                        }}
                      >
                        <Shield style={{ width: '12px', height: '12px' }} />
                        {member.role}
                      </span>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <span 
                        className={`inline-flex items-center rounded-full font-medium ${getStatusColor(member.status)}`}
                        style={{ 
                          padding: '4px 10px',
                          fontSize: '12px'
                        }}
                      >
                        {member.status}
                      </span>
                    </td>
                    <td 
                      className="text-slate-600"
                      style={{ padding: '16px 24px', fontSize: '14px' }}
                    >
                      {member.joinDate}
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      {member.role !== 'Owner' && (
                        <button 
                          onClick={() => removeMember(member.id)}
                          className="text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          style={{ padding: '8px' }}
                        >
                          <Trash2 style={{ width: '16px', height: '16px' }} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div 
          className="bg-white rounded-2xl shadow-sm border border-slate-200 text-center"
          style={{ padding: '48px' }}
        >
          <div 
            className="bg-slate-100 rounded-2xl flex items-center justify-center mx-auto"
            style={{ 
              width: '64px', 
              height: '64px',
              marginBottom: '16px'
            }}
          >
            <Users className="text-slate-500" style={{ width: '32px', height: '32px' }} />
          </div>
          <h3 
            className="font-semibold text-slate-900"
            style={{ fontSize: '20px', lineHeight: '28px', marginBottom: '8px' }}
          >
            You're the only member
          </h3>
          <p 
            className="text-slate-600"
            style={{ fontSize: '16px', marginBottom: '24px' }}
          >
            Invite your team members to collaborate on your chatbot
          </p>
          <Button 
            className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium"
            style={{ padding: '12px 24px' }}
          >
            <UserPlus style={{ width: '20px', height: '20px', marginRight: '8px' }} />
            Invite Your Team
          </Button>
        </div>
      )}
    </div>
  );
};
