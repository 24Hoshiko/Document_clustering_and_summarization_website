import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import FileUpload from "./components/FileUpload";
import Clusters from "./components/Clusters";
import TextView from "./components/TextView";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<FileUpload />} />
        <Route path="/clusters" element={<Clusters />} />
        <Route path="/text/:category/:filename" element={<TextView />} /> {/* New route */}
      </Routes>
    </Router>
  );
}

export default App;
