"use client"; // Mark this as a Client Component
import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

const SubdomainSearch = () => {
  const [domain, setDomain] = useState("");
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState("");
  const eventSourceRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResults([]);
    setError(null);
    setIsLoading(true);
    setDebugInfo("");

    // Close any existing EventSource
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/cyberAttack/search-subdomains/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ domain }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const decodedChunk = decoder.decode(value, { stream: true });
        const events = decodedChunk.split("\n\n").filter(Boolean);

        events.forEach((event) => {
          if (event.startsWith("data: ")) {
            const jsonData = event.replace("data: ", "");
            try {
              const result = JSON.parse(jsonData);
              setResults((prevResults) => [...prevResults, result]);
            } catch (e) {
              setDebugInfo((prev) => prev + `\nInvalid JSON: ${jsonData}`);
            }
          }
        });
      }
    } catch (err) {
      setError(`An error occurred: ${err.message}`);
      setDebugInfo((prev) => prev + `\nError details: ${err.toString()}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-3xl font-bold text-center mb-6">
        Live Subdomain Search
      </h1>

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
      {debugInfo && (
        <pre className="mt-4 p-4 bg-gray-100 rounded overflow-auto text-sm">
          {debugInfo}
        </pre>
      )}

      <div className="mt-8">
        {results.length > 0 ? (
          <ul className="space-y-4">
            {results.map((result, index) => (
              <li
                key={index}
                className="p-4 border border-gray-300 rounded-md bg-white shadow-sm"
              >
                <h2 className="text-xl font-semibold mb-2">
                  Subdomain: {result.subdomain}
                </h2>
                <p className="mb-2">
                  <strong>Status:</strong> {result.status}
                </p>
                <p className="mb-2">
                  <strong>IP:</strong> {result.ip || "N/A"}
                </p>
                <div>
                  <strong>Open Ports:</strong>
                  <ul className="list-disc pl-5">
                    {result.open_ports &&
                      result.open_ports.map((port, i) => (
                        <li key={i}>
                          Port {port.port}: {port.service} (Version:{" "}
                          {port.version})
                        </li>
                      ))}
                  </ul>
                </div>
                <div className="mt-4">
                  <ReactMarkdown>
                    {result.crawled_pages.join("\n")}
                  </ReactMarkdown>
                </div>
                <div className="mt-4">
                  <ReactMarkdown>
                    {result.technologies.join("\n")}
                  </ReactMarkdown>
                </div>
                <div className="mt-4">
                  <ReactMarkdown>{result.gemini_analysis}</ReactMarkdown>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          !isLoading && <p className="text-center">No results found</p>
        )}
      </div>
    </div>
  );
};

export default SubdomainSearch;
