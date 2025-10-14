
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ReduxProvider } from "@/store/ReduxProvider";
import { ProtectedRoute } from "@/components/common/ProtectedRoute";
import { PublicRoute } from "@/components/common/PublicRoute";
import { AuthInitializer } from "@/components/common/AuthInitializer";
import { ScrollToTop } from "@/components/common/ScrollToTop";
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

const App = () => (
  // test
  <ReduxProvider>
    <TooltipProvider>
        <Toaster />
        <Sonner />
        <AuthInitializer>
          <BrowserRouter>
            <ScrollToTop />
            <Routes>
          {/* Public Routes - redirect to dashboard if already authenticated */}
          <Route path="/login" element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          } />
          <Route path="/signup" element={
            <PublicRoute>
              <SignupPage />
            </PublicRoute>
          } />
          <Route path="/forgot-password" element={
            <PublicRoute>
              <ForgotPasswordPage />
            </PublicRoute>
          } />
          <Route path="/reset-password" element={
            <PublicRoute>
              <ResetPasswordPage />
            </PublicRoute>
          } />
          
          {/* Root redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* Protected Routes - require authentication */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <DashboardLayout>
                <DashboardPage />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          <Route path="/documents" element={
            <ProtectedRoute>
              <DashboardLayout>
                <DocumentsPage />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          <Route path="/chatbot" element={
            <ProtectedRoute>
              <DashboardLayout>
                <ChatbotPage />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          <Route path="/analytics" element={
            <ProtectedRoute>
              <DashboardLayout>
                <AnalyticsPage />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          <Route path="/documentation" element={
            <ProtectedRoute>
              <DashboardLayout>
                <DocumentationPage />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          <Route path="/api-keys" element={
            <ProtectedRoute>
              <DashboardLayout>
                <ApiKeysPage />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          <Route path="/team" element={
            <ProtectedRoute>
              <DashboardLayout>
                <TeamPage />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          <Route path="/billing" element={
            <ProtectedRoute>
              <DashboardLayout>
                <BillingPage />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute>
              <DashboardLayout>
                <SettingsPage />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute>
              <DashboardLayout>
                <ProfilePage />
              </DashboardLayout>
            </ProtectedRoute>
          } />
          
          {/* Catch all route */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthInitializer>
    </TooltipProvider>
  </ReduxProvider>
);

export default App;
