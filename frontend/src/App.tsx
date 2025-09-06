
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { DashboardLayout } from "./components/layout/DashboardLayout";
import { LoginPage } from "./components/auth/LoginPage";
import { SignupPage } from "./components/auth/SignupPage";
import { ForgotPasswordPage } from "./components/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "./components/auth/ResetPasswordPage";
import { DashboardPage } from "./components/pages/DashboardPage";
import { DocumentsPage } from "./components/pages/DocumentsPage";
import { ChatbotPage } from "./components/pages/ChatbotPage";
import { AnalyticsPage } from "./components/pages/AnalyticsPage";
import { DocumentationPage } from "./components/pages/DocumentationPage";
import { ApiKeysPage } from "./components/pages/ApiKeysPage";
import { TeamPage } from "./components/pages/TeamPage";
import { SettingsPage } from "./components/pages/SettingsPage";
import { ProfilePage } from "./components/pages/ProfilePage";
import NotFound from "./pages/NotFound";
import { BillingPage } from "./components/pages/BillingPage";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={
            <DashboardLayout>
              <DashboardPage />
            </DashboardLayout>
          } />
          <Route path="/documents" element={
            <DashboardLayout>
              <DocumentsPage />
            </DashboardLayout>
          } />
          <Route path="/chatbot" element={
            <DashboardLayout>
              <ChatbotPage />
            </DashboardLayout>
          } />
          <Route path="/analytics" element={
            <DashboardLayout>
              <AnalyticsPage />
            </DashboardLayout>
          } />
          <Route path="/documentation" element={
            <DashboardLayout>
              <DocumentationPage />
            </DashboardLayout>
          } />
          <Route path="/api-keys" element={
            <DashboardLayout>
              <ApiKeysPage />
            </DashboardLayout>
          } />
          <Route path="/team" element={
            <DashboardLayout>
              <TeamPage />
            </DashboardLayout>
          } />
          <Route path="/billing" element={
            <DashboardLayout>
              <BillingPage />
            </DashboardLayout>
          } />
          <Route path="/settings" element={
            <DashboardLayout>
              <SettingsPage />
            </DashboardLayout>
          } />
          <Route path="/profile" element={
            <DashboardLayout>
              <ProfilePage />
            </DashboardLayout>
          } />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
