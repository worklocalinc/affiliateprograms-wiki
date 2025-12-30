import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import ProgramPage from "./pages/ProgramPage";
import NetworkPage from "./pages/NetworkPage";
import NichePage from "./pages/NichePage";
import ComparisonPage from "./pages/ComparisonPage";
import ProgramsListPage from "./pages/ProgramsListPage";
import NetworksListPage from "./pages/NetworksListPage";
import NichesListPage from "./pages/NichesListPage";
import ComparisonsListPage from "./pages/ComparisonsListPage";
import CountriesListPage from "./pages/CountriesListPage";
import CountryPage from "./pages/CountryPage";
import AboutPage from "./pages/AboutPage";
import ToolsPage from "./pages/ToolsPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/programs" element={<ProgramsListPage />} />
          <Route path="/programs/:slug" element={<ProgramPage />} />
          <Route path="/networks" element={<NetworksListPage />} />
          <Route path="/networks/:slug" element={<NetworkPage />} />
          <Route path="/niches" element={<NichesListPage />} />
          <Route path="/niches/:slug" element={<NichePage />} />
          <Route path="/countries" element={<CountriesListPage />} />
          <Route path="/countries/:country" element={<CountryPage />} />
          <Route path="/comparisons" element={<ComparisonsListPage />} />
          <Route path="/comparisons/:slug" element={<ComparisonPage />} />
          <Route path="/tools" element={<ToolsPage />} />
          <Route path="/about" element={<AboutPage />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
