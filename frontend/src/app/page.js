"use client"; // Mark this as a Client Component

import { useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

const SubdomainSearch = () => {
  const [domain, setDomain] = useState("");
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const handleSubmit = async (e) => {
    e.preventDefault();
    setResults(null);
    setError(null);
    setIsLoading(true);

    try {
      const respons = await axios.post(
        `${apiUrl}/b/subdomain-search/`,
        { domain }, // Sending the domain in the request body
        {
          headers: {
            "Content-Type": "application/json", // Set appropriate headers
          },
        }
      );
    } catch (err) {
      console.error(err);
      setIsLoading(false);
    }

    try {
      const response = await axios.get(`${apiUrl}/b/subdomain/${domain}/`);

      setResults(response.data);
      setIsLoading(false);
    } catch (err) {
      console.error(err);
      setError("An error occurred while searching for subdomains.");
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-3xl font-bold text-center mb-6">Subdomain Search</h1>

      <form
        onSubmit={handleSubmit}
        className="bg-white shadow-lg rounded-lg p-6 space-y-4"
      >
        <input
          type="text"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          placeholder="Enter domain"
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <button
          type="submit"
          disabled={isLoading}
          className={`w-full py-2 px-4 rounded-md text-white font-semibold ${
            isLoading
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {isLoading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <p className="text-red-500 text-center mt-4">{error}</p>}

      {results && (
        <div className="mt-8">
          <h2 className="text-2xl font-bold mb-4">
            Results for {results.name}
          </h2>
          <p>Status: {results.status}</p>
          <p>Created at: {new Date(results.created_at).toLocaleString()}</p>

          {results.subdomains.map((subdomain, index) => (
            <div key={index} className="bg-white shadow-md rounded-md p-4 mb-6">
              <h3 className="text-xl font-semibold">
                Subdomain: {subdomain.name}
              </h3>
              <p>IP: {subdomain.ip}</p>
              <p>Status: {subdomain.status}</p>
              <p>
                Created at: {new Date(subdomain.created_at).toLocaleString()}
              </p>

              {/* Open Ports */}
              <h4 className="font-semibold mt-2">Open Ports:</h4>
              {subdomain.open_ports && subdomain.open_ports.length > 0 ? (
                subdomain.open_ports.map((port, portIndex) => (
                  <div key={portIndex} className="ml-4">
                    <p>Port: {port.port}</p>
                    <p>Status: {port.status}</p>
                    <p>Service: {port.service}</p>
                    <p>Version: {port.version}</p>
                    <hr className="my-2" />
                  </div>
                ))
              ) : (
                <p className="ml-4">No open ports found.</p>
              )}

              {/* Technologies */}
              <h4 className="font-semibold mt-2">Technologies:</h4>
              {subdomain.technologies && subdomain.technologies.length > 0 ? (
                <ul className="ml-4 list-disc">
                  {subdomain.technologies.map((tech, techIndex) => (
                    <li key={techIndex}>{tech.name}</li>
                  ))}
                </ul>
              ) : (
                <p className="ml-4">No technologies found.</p>
              )}

              {/* Crawled Pages */}
              <h4 className="font-semibold mt-2">Crawled Pages:</h4>
              {subdomain.crawled_pages && subdomain.crawled_pages.length > 0 ? (
                <ul className="ml-4 list-disc">
                  {subdomain.crawled_pages.map((page, pageIndex) => (
                    <li key={pageIndex}>
                      {page.url} (Status: {page.status_code}, Title:{" "}
                      {page.title})
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="ml-4">No crawled pages found.</p>
              )}

              {/* Gemini Analysis */}
              <h4 className="font-semibold mt-2">Gemini Analysis:</h4>
              <ReactMarkdown className="ml-4">
                {subdomain.gemini_analysis}
              </ReactMarkdown>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SubdomainSearch;
