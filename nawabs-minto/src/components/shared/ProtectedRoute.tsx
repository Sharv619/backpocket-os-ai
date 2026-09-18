import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";

export function ProtectedRoute({
  isAllowed,
  isLoading,
  redirectTo,
  children,
}: {
  isAllowed: boolean;
  isLoading: boolean;
  redirectTo: string;
  children: ReactNode;
}) {
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-nawab-cream text-nawab-maroon-600">
        Loading…
      </div>
    );
  }
  if (!isAllowed) {
    return <Navigate to={redirectTo} replace />;
  }
  return <>{children}</>;
}
