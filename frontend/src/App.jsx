import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import AppLayout from "./components/layout/AppLayout";

import Dashboard from "./pages/Dashboard";
import Persona from "./pages/Persona";
import Posts from "./pages/Posts";
import Activity from "./pages/Activity";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/persona" element={<Persona />} />
          <Route path="/posts" element={<Posts />} />
          <Route path="/activity" element={<Activity />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}