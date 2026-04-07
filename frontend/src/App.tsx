import { Navigate, Route, Routes } from "react-router-dom";

import { LayoutShell } from "./components/LayoutShell";
import { AuditDetailPage } from "./pages/AuditDetailPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { MetricReferencePage } from "./pages/MetricReferencePage";
import { NewAuditPage } from "./pages/NewAuditPage";
import { RegisterPage } from "./pages/RegisterPage";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<LayoutShell />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/audits/new" element={<NewAuditPage />} />
        <Route path="/audits/:id" element={<AuditDetailPage />} />
        <Route path="/metrics" element={<MetricReferencePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
