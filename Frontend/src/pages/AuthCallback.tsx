// src/pages/AuthCallback.tsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function AuthCallback() {
  const navigate = useNavigate();
  const { saveOAuthLogin } = useAuth();

  useEffect(() => {
    console.log("🔵 AuthCallback - Starting OAuth processing");
    console.log("🔵 Full URL:", window.location.href);
    
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const profileParam = params.get("profile");

    console.log("🔵 Token found:", !!token);
    console.log("🔵 Profile param found:", !!profileParam);

    if (token && profileParam) {
      try {
        const profile = JSON.parse(decodeURIComponent(profileParam));
        console.log("✅ Decoded profile:", profile);

        // Save to context and localStorage
        saveOAuthLogin(token, profile);
        
        console.log("✅ OAuth saved, redirecting to dashboard...");
        
        // Small delay to ensure state updates
        setTimeout(() => {
          navigate("/dashboard", { replace: true });
        }, 100);
        
      } catch (error) {
        console.error("❌ Error processing OAuth:", error);
        navigate("/login", { replace: true });
      }
    } else {
      console.error("❌ Missing token or profile");
      navigate("/login", { replace: true });
    }
  }, [navigate, saveOAuthLogin]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">
          Completing Sign In...
        </h2>
        <p className="text-gray-600 dark:text-gray-400">Please wait while we log you in</p>
      </div>
    </div>
  );
}