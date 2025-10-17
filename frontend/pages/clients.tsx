import useSWR from "swr";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Layout from "../components/Layout";
import { useAuth } from "../utils/authContext";
import { apiClient, APIClientError } from "../utils/apiBase";
import { AuthErrorDisplay } from "../components/AuthErrorDisplay";

const fetcher = async (url: string) => {
  try {
    return await apiClient.get(url);
  } catch (error) {
    if (error instanceof APIClientError && error.isAuthError) {
      throw error;
    }
    throw error;
  }
};

export default function Clients() {
  const {
    isAuthenticated,
    isLoading: authLoading,
    error: authError,
    user,
  } = useAuth();
  const [clientName, setClientName] = useState("");
  const router = useRouter();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, authLoading, router]);

  // Redirect non-admins
  useEffect(() => {
    if (!authLoading && isAuthenticated && user?.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [user, isAuthenticated, authLoading, router]);

  const {
    data: clients,
    error: clientsError,
    mutate,
  } = useSWR(isAuthenticated && user?.role === "admin" ? "/api/clients" : null, fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: true,
    errorRetryCount: 3,
  });

  const createClient = async () => {
    if (!clientName.trim()) {
      alert("Please enter a client name");
      return;
    }

    try {
      await apiClient.post("/api/clients", {
        name: clientName.trim(),
      });

      setClientName("");
      mutate();
      alert("Client created successfully!");
    } catch (error) {
      console.error("Create client error:", error);
      if (error instanceof APIClientError) {
        alert(`Failed to create client: ${error.message}`);
      } else {
        alert("Error creating client");
      }
    }
  };

  // Show loading state during authentication check
  if (authLoading) {
    return (
      <Layout>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      </Layout>
    );
  }

  // Don't render if not authenticated or not admin
  if (!isAuthenticated || user?.role !== "admin") {
    return null;
  }

  return (
    <Layout>
      <h2 className="text-lg font-semibold mb-3">Client Management</h2>
      <p className="text-sm text-gray-600 mb-6">
        Create and manage clients. Each client can have their own configurations and users.
      </p>

      {/* Authentication Error Display */}
      {authError && (
        <AuthErrorDisplay
          error={authError}
          onLogin={() => router.push("/")}
          className="mb-4"
        />
      )}

      {/* Client Creation Error */}
      {clientsError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-red-600">
            Error loading clients: {clientsError.message}
          </p>
        </div>
      )}

      {/* Create Client Form */}
      <div className="bg-white border rounded-xl p-4 shadow-sm mb-4">
        <h3 className="font-medium mb-3">Add New Client</h3>
        <div className="flex gap-3">
          <input
            className="flex-1 border rounded-md px-3 py-2"
            placeholder="Enter client name (e.g., Acme Corp)"
            value={clientName}
            onChange={(e) => setClientName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") {
                createClient();
              }
            }}
          />
          <button
            className="px-4 py-2 rounded-md bg-black text-white hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={createClient}
            disabled={!clientName.trim()}
          >
            Create Client
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Client names should be unique and descriptive
        </p>
      </div>

      {/* Clients List */}
      <div className="bg-white border rounded-xl p-4 shadow-sm">
        <h3 className="font-medium mb-3">Existing Clients</h3>
        {!clients ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading clients...</p>
          </div>
        ) : Array.isArray(clients) && clients.length > 0 ? (
          <div className="grid gap-3">
            {clients.map((client: any) => (
              <div key={client.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-lg">{client.name}</div>
                    <div className="text-sm text-gray-500">
                      ID: {client.id} • Slug: {client.slug}
                    </div>
                    {client.created_at && (
                      <div className="text-xs text-gray-400 mt-1">
                        Created: {new Date(client.created_at).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <span className="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800">
                      Active
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-600">
            No clients yet. Create your first client above.
          </div>
        )}
      </div>
    </Layout>
  );
}
