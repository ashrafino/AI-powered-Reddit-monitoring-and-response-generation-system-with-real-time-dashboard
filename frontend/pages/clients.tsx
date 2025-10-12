import useSWR from "swr";
import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Layout from "../components/Layout";
import { useAuth } from "../utils/authContext";
import { apiClient, APIClientError } from "../utils/apiBase";

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
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const router = useRouter();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, authLoading, router]);

  // Redirect if not admin
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
    if (!name.trim()) {
      alert("Please enter a client name");
      return;
    }

    try {
      await apiClient.post("/api/clients", {
        name: name.trim(),
        description: description.trim() || null,
      });

      setName("");
      setDescription("");
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
        Manage clients for your Reddit monitoring system
      </p>

      {/* Create Client Form */}
      <div className="bg-white border rounded-xl p-4 shadow-sm mb-4">
        <h3 className="font-medium mb-3">Add New Client</h3>
        <div className="grid gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Client Name <span className="text-red-500">*</span>
            </label>
            <input
              className="w-full border rounded-md px-3 py-2"
              placeholder="e.g., Acme Corporation"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <p className="text-xs text-gray-500 mt-1">
              The name of the client or organization
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <textarea
              className="w-full border rounded-md px-3 py-2"
              placeholder="Brief description of the client..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
            <p className="text-xs text-gray-500 mt-1">
              Additional information about this client
            </p>
          </div>

          <div className="flex justify-end">
            <button
              className="px-4 py-2 rounded-md bg-black text-white hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={createClient}
              disabled={!name.trim()}
            >
              Create Client
            </button>
          </div>
        </div>
      </div>

      {/* Clients List */}
      <div className="bg-white border rounded-xl p-4 shadow-sm">
        <h3 className="font-medium mb-3">Existing Clients</h3>

        {clientsError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <p className="text-red-600">
              Error loading clients: {clientsError.message}
            </p>
          </div>
        )}

        {!clients ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading clients...</p>
          </div>
        ) : Array.isArray(clients) && clients.length > 0 ? (
          <div className="grid gap-3">
            {clients.map((client: any) => (
              <div key={client.id} className="border rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-lg">{client.name}</h4>
                      <span className="text-xs text-gray-500">ID: {client.id}</span>
                    </div>
                    {client.description && (
                      <p className="text-sm text-gray-600 mt-1">
                        {client.description}
                      </p>
                    )}
                    <div className="mt-2 text-xs text-gray-500">
                      Slug: {client.slug}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-4 text-gray-600">
            No clients yet. Create your first client above.
          </div>
        )}
      </div>
    </Layout>
  );
}
