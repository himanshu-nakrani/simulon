import { useState } from 'react';
import InputForm from './components/InputForm';
import ResultsPage from './components/ResultsPage';

export default function App() {
  const [result, setResult] = useState(null);

  if (result) {
    return <ResultsPage result={result} onBack={() => setResult(null)} />;
  }

  return <InputForm onResult={setResult} />;
}
