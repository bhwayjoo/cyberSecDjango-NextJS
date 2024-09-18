import React, { useState, useCallback, useEffect } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

const SubdomainSearch = () => {
  const [domain, setDomain] = useState("");
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [searchStatus, setSearchStatus] = useState(null);

  const apiUrl =
    "https://0471a463-7b15-4181-a9c5-3bfd4aac048d-dev.e1-eu-north-azure.choreoapis.dev/djangoxreact/backendd/v1.0";

  const fetchResults = useCallback(async () => {
    try {
      const response = await axios.get(`${apiUrl}/b/subdomain/${domain}/`);
      setResults(response.data);
      setSearchStatus(response.data.status);
      return response.data.status;
    } catch (err) {
      console.error("Error fetching results:", err);
      setError("An error occurred while fetching results. Retrying...");
      return "error";
    }
  }, [apiUrl, domain]);

  const startPolling = useCallback(() => {
    const pollInterval = setInterval(async () => {
      const status = await fetchResults();
      if (status === "complete") {
        clearInterval(pollInterval);
        setIsLoading(false);
      }
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [fetchResults]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResults(null);
    setError(null);
    setIsLoading(true);
    setSearchStatus("in_progress");

    try {
      axios.post(
        `${apiUrl}/b/subdomain-search/`,
        { domain },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      startPolling();
    } catch (err) {
      console.error("Error initiating subdomain search:", err);
      setError(
        "An error occurred while initiating the subdomain search. Retrying..."
      );
      startPolling();
    }
  };

  // Rendering functions
  const renderOpenPorts = (ports) => {
    if (!ports || ports.length === 0) {
      return <p className="ml-4">No open ports found.</p>;
    }

    return ports.map((port, index) => (
      <div key={index} className="ml-4 mb-2">
        <p>Port: {port.port}</p>
        <p>Status: {port.status}</p>
        <p>Service: {port.service}</p>
        <p>Version: {port.version}</p>
      </div>
    ));
  };

  const renderTechnologies = (technologies) => {
    if (!technologies || technologies.length === 0) {
      return <p className="ml-4">No technologies found.</p>;
    }

    return (
      <ul className="ml-4 list-disc">
        {technologies.map((tech, index) => (
          <li key={index}>{tech.name}</li>
        ))}
      </ul>
    );
  };

  const renderCrawledPages = (pages) => {
    if (!pages || pages.length === 0) {
      return <p className="ml-4">No crawled pages found.</p>;
    }

    return (
      <ul className="ml-4 list-disc">
        {pages.map((page, index) => (
          <li key={index}>
            {page.url} (Status: {page.status_code}, Title: {page.title})
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="min-h-screen flex justify-center items-center">
      <div className="flex flex-col items-center bg-white p-6 rounded-lg shadow-lg w-full max-w-4xl">
        <h1 className="text-3xl font-bold text-center mb-6">
          Subdomain Search
        </h1>

        <form onSubmit={handleSubmit} className="w-full mb-6">
          <div className="flex items-center border-b border-b-2 border-blue-500 py-2">
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="Enter domain"
              className="appearance-none bg-transparent border-none w-full text-gray-700 mr-3 py-1 px-2 leading-tight focus:outline-none"
            />
            <button
              type="submit"
              disabled={isLoading}
              className={`flex-shrink-0 ${
                isLoading
                  ? "bg-blue-300 cursor-not-allowed"
                  : "bg-blue-500 hover:bg-blue-700"
              } text-sm text-white py-1 px-2 rounded`}
            >
              {isLoading ? "Searching..." : "Search"}
            </button>
          </div>
        </form>

        {error && <p className="text-red-500 text-center mt-4">{error}</p>}

        {isLoading && (
          <div className="flex justify-center items-center">
            <svg
              className="animate-spin h-10 w-10 text-blue-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zM2 12a10 10 0 0110-10V0C4.477 0 0 4.477 0 10h2z"
              ></path>
            </svg>
          </div>
        )}

        {searchStatus && (
          <p className="text-center mt-4">
            Search status:{" "}
            {searchStatus === "in_progress" ? "In progress..." : searchStatus}
          </p>
        )}

        {results && (
          <div className="mt-8 w-full">
            <h2 className="text-2xl font-bold mb-4">
              Results for {results.name}
            </h2>
            <p>Status: {results.status}</p>
            <p>Created at: {new Date(results.created_at).toLocaleString()}</p>

            {results.subdomains.map((subdomain, index) => (
              <div
                key={index}
                className="bg-white shadow-md rounded-md p-4 mb-6"
              >
                <h3 className="text-xl font-semibold">
                  Subdomain: {subdomain.name}
                </h3>
                <p>IP: {subdomain.ip}</p>
                <p>Status: {subdomain.status}</p>
                <p>
                  Created at: {new Date(subdomain.created_at).toLocaleString()}
                </p>

                <h4 className="font-semibold mt-2">Open Ports:</h4>
                {renderOpenPorts(subdomain.open_ports)}

                <h4 className="font-semibold mt-2">Technologies:</h4>
                {renderTechnologies(subdomain.technologies)}

                <h4 className="font-semibold mt-2">Crawled Pages:</h4>
                {renderCrawledPages(subdomain.crawled_pages)}

                <h4 className="font-semibold mt-2">Gemini Analysis:</h4>
                <ReactMarkdown className="ml-4">
                  {subdomain.gemini_analysis}
                </ReactMarkdown>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SubdomainSearch;
