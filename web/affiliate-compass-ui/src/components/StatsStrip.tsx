import { Database, Building2, RefreshCw, Calendar } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";

type StatsResponse = {
  programs: number;
  cpa_networks: number;
  deep_researched: number;
  has_commission: number;
  generated_at: string;
};

export function StatsStrip() {
  const { data } = useQuery({
    queryKey: ["stats"],
    queryFn: () => apiGet<StatsResponse>("/stats"),
    staleTime: 30_000,
  });

  const stats = [
    { label: "Programs Indexed", value: data?.programs?.toLocaleString() ?? "—", icon: Database },
    { label: "Deep Researched", value: data?.deep_researched?.toLocaleString() ?? "—", icon: RefreshCw },
    { label: "CPA Networks", value: data?.cpa_networks?.toLocaleString() ?? "—", icon: Building2 },
    { label: "Last Updated", value: data?.generated_at ? new Date(data.generated_at).toLocaleDateString() : "—", icon: Calendar },
  ];

  return (
    <div className="bg-secondary/50 border-y border-border">
      <div className="container py-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="flex items-center justify-center gap-2 mb-1">
                <stat.icon className="w-4 h-4 text-primary" />
                <span className="text-2xl font-semibold text-foreground">{stat.value}</span>
              </div>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
