import { ThemeProvider } from './contexts/ThemeContext';
import { CLPProvider } from './contexts/CLPContext';
import { QuadroGeracao } from './components/Supervisorio/QuadroGeracao';
import './App.css';

function App() {
  return (
    <ThemeProvider>
      <CLPProvider>
        <QuadroGeracao />
      </CLPProvider>
    </ThemeProvider>
  );
}

export default App;
