import { AnalysisProvider } from "./context/AnalysisContext";
import { Dashboard } from "./pages/Dashboard";

function App() {
  return (
    <AnalysisProvider>
      <Dashboard />
    </AnalysisProvider>
  );
}

export default App;