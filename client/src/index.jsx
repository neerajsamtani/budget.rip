import React from "react";
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import App from "./App";
import { LineItemsProvider } from "./contexts/LineItemsContext";
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const container = document.getElementById("root");
const root = createRoot(container);
root.render(
    <QueryClientProvider client={queryClient}>
      <LineItemsProvider>
        <App />
      </LineItemsProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
);