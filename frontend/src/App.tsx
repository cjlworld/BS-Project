import { HashRouter, Route, Routes } from "react-router-dom";
import SearchPage from "./pages/SearchPage";
import LoginPage from "./pages/LoginPage";
import SignUpPage from "./pages/SignUpPage";
import GoodDetail from "./pages/GoodDetail";

function App() {
  return (
    <div className="min-h-screen bg-[url('./background.png')] bg-cover bg-center bg-fixed">
      <HashRouter>
        <Routes>
          <Route path="/" Component={SearchPage} />
          <Route path="/login" Component={LoginPage} />
          <Route path="/signup" Component={SignUpPage} />
          <Route path="/good-detail/:id" Component={GoodDetail} />
        </Routes>
      </HashRouter>
    </div>
  );
}


export default App;