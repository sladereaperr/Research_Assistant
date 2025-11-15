// API configuration utility
// In development, uses proxy from vite.config.js
// In production, uses VITE_API_URL environment variable

const getApiUrl = () => {
  // In production, use environment variable if set
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // In development, use relative path (will be proxied by Vite)
  // In production build, this will be relative to the domain
  return "";
};

export const API_BASE_URL = getApiUrl();

export const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  return fetch(url, options);
};

