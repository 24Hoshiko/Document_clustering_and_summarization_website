import { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import "./style.css";

export default function FileUpload() {
  const [files, setFiles] = useState([]);
  const navigate = useNavigate();

  const handleFileChange = (event) => {
    const selectedFiles = Array.from(event.target.files);
    setFiles(selectedFiles);
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      alert("Please select files to upload.");
      return;
    }

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      const response = await fetch("http://localhost:8000/upload/", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        alert("Files uploaded and clustered successfully!");
        navigate("/clusters");
      } else {
        alert("Failed to upload files.");
      }
    } catch (error) {
      console.error("Error uploading files:", error);
      alert("An error occurred. Please try again.");
    }
  };

  return (
    <div className="upload-container">
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="heading"
      >
        Upload Your Documents
      </motion.h2>
      <div className="input-wrapper">
        <input
          type="file"
          multiple
          webkitdirectory="true"
          directory="true"
          onChange={handleFileChange}
          className="file-input"
        />
      </div>
      <motion.button
        className="upload-btn"
        onClick={handleUpload}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        Upload Files
      </motion.button>
      {files.length > 0 && (
        <div className="file-list">
          <p className="file-list-title">Selected Files:</p>
          {files.map((file, index) => (
            <p key={index} className="file-name">
              📄 {file.webkitRelativePath || file.name}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}