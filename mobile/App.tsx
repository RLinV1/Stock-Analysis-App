import PortfolioApp from './src/PortfolioApp';

// The root component takes no props; tests inject a client through PortfolioApp directly.
export default function App() {
  return <PortfolioApp />;
}
