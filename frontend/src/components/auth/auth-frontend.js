// src/auth/auth0-config.js
export const auth0Config = {
  domain: process.env.REACT_APP_AUTH0_DOMAIN,
  clientId: process.env.REACT_APP_AUTH0_CLIENT_ID,
  audience: process.env.REACT_APP_AUTH0_AUDIENCE,
  redirectUri: window.location.origin
};

// src/context/AuthContext.js
import React, { createContext, useContext, useEffect, useState } from 'react';
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';
import { auth0Config } from '../auth/auth0-config';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  return (
    <Auth0Provider
      domain={auth0Config.domain}
      clientId={auth0Config.clientId}
      redirectUri={auth0Config.redirectUri}
      audience={auth0Config.audience}
    >
      <AuthStateProvider>{children}</AuthStateProvider>
    </Auth0Provider>
  );
};

const AuthStateProvider = ({ children }) => {
  const { isLoading, isAuthenticated, user, getAccessTokenSilently } = useAuth0();
  const [authToken, setAuthToken] = useState(null);

  useEffect(() => {
    const getToken = async () => {
      try {
        if (isAuthenticated) {
          const token = await getAccessTokenSilently();
          setAuthToken(token);
        }
      } catch (error) {
        console.error('Error getting token:', error);
      }
    };

    getToken();
  }, [isAuthenticated, getAccessTokenSilently]);

  return (
    <AuthContext.Provider
      value={{
        isLoading,
        isAuthenticated,
        user,
        authToken
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// src/components/auth/LoginButton.jsx
import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const LoginButton = () => {
  const { loginWithRedirect } = useAuth0();

  return (
    <button
      onClick={() => loginWithRedirect()}
      className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
    >
      Log In
    </button>
  );
};

export default LoginButton;

// src/components/auth/LogoutButton.jsx
import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const LogoutButton = () => {
  const { logout } = useAuth0();

  return (
    <button
      onClick={() => logout({ returnTo: window.location.origin })}
      className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded"
    >
      Log Out
    </button>
  );
};

export default LogoutButton;

// src/services/api.js
import { useAuth } from '../context/AuthContext';

export const useApi = () => {
  const { authToken } = useAuth();

  const fetchWithAuth = async (endpoint, options = {}) => {
    if (!authToken) {
      throw new Error('No access token available');
    }

    const headers = {
      ...options.headers,
      Authorization: `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    };

    const response = await fetch(`/api${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  };

  return { fetchWithAuth };
};
