import { AnalysisProvider } from "./Services/Context/AnalyseCont";
import { Dashboard } from "./Pages/Dashboard";

function App() {
  return (
    <AnalysisProvider>
      <Dashboard />
    </AnalysisProvider>
  );
}

export default App;