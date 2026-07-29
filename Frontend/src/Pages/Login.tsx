import { useState } from "react";
import { useAuth } from "../Services/Context/AuthContext";
import { Link, useNavigate } from "react-router-dom";

export const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Email ou mot de passe incorrect");
    }
  };

  return (
    <div className="min-h-screen bg-dark flex items-center justify-center p-6">
      <div className="glass rounded-2xl p-8 w-full max-w-md">
        <div className="flex items-center gap-2 mb-8 justify-center">
          <div className="w-8 h-8 bg-cyan-500 rounded-lg flex items-center justify-center font-bold text-dark">L</div>
          <h1 className="text-2xl font-bold text-white">LucidAI</h1>
        </div>
        <h2 className="text-lg text-gray-300 mb-6 text-center">Connexion</h2>
        {error && <p className="text-danger text-sm mb-4 text-center">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-3 rounded-xl bg-dark-card border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
            required
          />
          <input
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-3 rounded-xl bg-dark-card border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
            required
          />
          <button type="submit" className="w-full bg-cyan-500 hover:bg-cyan-600 text-dark font-bold py-3 rounded-xl transition-colors">
            Se connecter
          </button>
        </form>
        <p className="text-gray-400 text-sm mt-6 text-center">
          Pas de compte ? <Link to="/register" className="text-cyan-400 hover:underline">S'inscrire</Link>
        </p>
      </div>
    </div>
  );
};
