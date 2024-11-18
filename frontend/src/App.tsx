import { HashRouter, Route, Routes } from "react-router-dom";
import SearchPage from "./pages/SearchPage";

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/">
          <SearchPage />
        </Route>
      </Routes>
    </HashRouter>
  );
}


export default App;