import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Document, Page, pdfjs } from "react-pdf";
import { useNavigate } from "react-router-dom"; // Import useNavigate
import "./style.css"; // Import the style.css file

// Set the worker for react-pdf
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

export default function Clusters() {
  const [clusters, setClusters] = useState({});
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate(); // Add useNavigate hook

  useEffect(() => {
    const pollClusters = async () => {
      setIsLoading(true);
      let attempts = 0;
      const maxAttempts = 30; // 30 seconds (1 second per attempt)

      while (attempts < maxAttempts) {
        try {
          const response = await fetch("http://localhost:8000/clusters/");
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          const data = await response.json();
          console.log("Fetched clusters:", data);
          if (Object.keys(data.clusters).length > 0) {
            setClusters(data.clusters);
            setError(null);
            setIsLoading(false);
            return;
          }
        } catch (err) {
          console.error("Error fetching clusters:", err);
          setError("Failed to load clusters. Please ensure the backend server is running.");
          setIsLoading(false);
          return;
        }
        attempts++;
        await new Promise((resolve) => setTimeout(resolve, 1000)); // Wait 1 second
      }
      setError("Clustering took too long. Please try again.");
      setIsLoading(false);
    };

    pollClusters();
  }, []);

  const handleSummarize = async (category) => {
    try {
      const response = await fetch(`http://localhost:8000/summarize/${category}`, {
        method: "POST",
      });
      if (response.ok) {
        alert("Summaries generated successfully!");
        fetchClusters();
      } else {
        alert("Failed to generate summaries.");
      }
    } catch (err) {
      console.error("Error summarizing:", err);
      alert("Failed to generate summaries.");
    }
  };

  const fetchClusters = async () => {
    try {
      const response = await fetch("http://localhost:8000/clusters/");
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      console.log("Fetched clusters:", data);
      setClusters(data.clusters);
      setError(null);
    } catch (err) {
      console.error("Error fetching clusters:", err);
      setError("Failed to load clusters. Please ensure the backend server is running.");
    }
  };

  const handleFileClick = async (category, filename) => {
    if (filename.endsWith(".txt")) {
      // Check if the file is differences.txt or similarities.txt
      if (filename === "differences.txt" || filename === "similarities.txt") {
        // Navigate to the new page
        navigate(`/text/${category}/${filename}`);
      } else {
        // Display other .txt files on the same page
        const response = await fetch(`http://localhost:8000/file/${category}/${filename}`);
        const text = await response.text();
        setSelectedFile({ type: "text", category, filename, content: text });
      }
    } else if (filename.endsWith(".pdf")) {
      const fileUrl = `http://localhost:8000/file/${category}/${filename}`;
      // Fetch the PDF as a blob to avoid CORS issues
      try {
        const response = await fetch(fileUrl);
        if (!response.ok) {
          throw new Error(`Failed to fetch PDF: ${response.statusText}`);
        }
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        setSelectedFile({ type: "pdf", category, filename, url: blobUrl, originalUrl: fileUrl });
      } catch (err) {
        console.error("Error fetching PDF:", err);
        // Fallback to opening in a new tab
        window.open(fileUrl, "_blank");
        setSelectedFile(null);
      }
    } else {
      window.open(`http://localhost:8000/file/${category}/${filename}`, "_blank");
    }
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const onDocumentLoadError = (error) => {
    console.error("Error loading PDF:", error);
    // Fallback to opening in a new tab if react-pdf fails
    if (selectedFile && selectedFile.originalUrl) {
      window.open(selectedFile.originalUrl, "_blank");
    }
    setSelectedFile(null);
  };

  return (
    <div className="clusters-container">
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        Clustered Research Papers
      </motion.h2>
      {isLoading && <p>Loading clusters, please wait...</p>}
      {error && <p className="error-message">{error}</p>}
      {!isLoading && Object.keys(clusters).length === 0 && !error ? (
        <p>No clusters found. Please upload some documents.</p>
      ) : (
        !isLoading &&
        Object.keys(clusters).map((category) => (
          <div key={category} className="cluster-section">
            <h3>{category}</h3>
            <ul className="file-list">
              {clusters[category].files.map((file) => (
                <li key={file} className="file-item">
                  <span onClick={() => handleFileClick(category, file)} className="file-link">
                    📄 {file}
                  </span>
                </li>
              ))}
            </ul>
            <motion.button
              className="summarize-btn"
              onClick={() => handleSummarize(category)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Summarize
            </motion.button>
          </div>
        ))
      )}
      {selectedFile && (
        <div className="output-container">
          <h4>{selectedFile.filename}</h4>
          {selectedFile.type === "text" ? (
            <div className="text-container">
              <pre>{selectedFile.content}</pre>
            </div>
          ) : (
            <div className="pdf-viewer">
              <Document
                file={selectedFile.url}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={onDocumentLoadError}
              >
                {Array.from(new Array(numPages), (el, index) => (
                  <Page key={`page_${index + 1}`} pageNumber={index + 1} />
                ))}
              </Document>
            </div>
          )}
          <button onClick={() => setSelectedFile(null)}>Close</button>
        </div>
      )}
    </div>
  );
}