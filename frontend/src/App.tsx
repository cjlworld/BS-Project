import { HashRouter, Route, Routes } from "react-router-dom";

import SearchPage from "./pages/SearchPage";
import LoginPage from "./pages/LoginPage";
import SignUpPage from "./pages/SignUpPage";
import GoodDetailPage from "./pages/GoodDetailPage";


function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" Component={SearchPage} />
        <Route path="/login" Component={LoginPage} />
        <Route path="/signup" Component={SignUpPage} />
        <Route path="/good-detail/:id" Component={GoodDetailPage} />
      </Routes>
    </HashRouter>
  );
}

export default App;