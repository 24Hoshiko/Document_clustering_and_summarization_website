import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./style.css"; // Import the style.css file

export default function TextView() {
  const { category, filename } = useParams(); // Get category and filename from URL
  const navigate = useNavigate();
  const [content, setContent] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTextContent = async () => {
      try {
        const response = await fetch(`http://localhost:8000/file/${category}/${filename}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch text file: ${response.statusText}`);
        }
        const text = await response.text();
        setContent(text);
      } catch (err) {
        console.error("Error fetching text file:", err);
        setError("Failed to load text file. Please try again.");
      }
    };

    fetchTextContent();
  }, [category, filename]);

  return (
    <div className="text-view-container">
      <h2>{filename}</h2>
      {error ? (
        <p className="error-message">{error}</p>
      ) : (
        <div className="text-container">
          <pre>{content}</pre>
        </div>
      )}
      <button onClick={() => navigate("/clusters")}>Back to Clusters</button>
    </div>
  );
}