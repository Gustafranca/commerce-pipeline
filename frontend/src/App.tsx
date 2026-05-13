import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { AppShell } from "./components/AppShell";
import { IngestPage } from "./pages/IngestPage";
import { StagedPage } from "./pages/StagedPage";
import { BrowsePage } from "./pages/BrowsePage";
import { ExplorerPage } from "./pages/ExplorerPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<IngestPage />} />
            <Route path="/staged" element={<StagedPage />} />
            <Route path="/browse" element={<BrowsePage />} />
            <Route path="/explorer" element={<ExplorerPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
