import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

interface NicheCardProps {
  name: string;
  slug: string;
  description: string;
  programCount: number;
  icon?: string;
}

export function NicheCard({ name, slug, description, programCount, icon }: NicheCardProps) {
  return (
    <Link
      to={`/niches/${slug}`}
      className="group block bg-card border border-border rounded-lg p-5 hover:shadow-md hover:border-primary/30 transition-all"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-2">
            {icon && <span className="text-2xl">{icon}</span>}
            <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
              {name}
            </h3>
          </div>
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{description}</p>
          <span className="text-sm font-medium text-primary">{programCount} programs</span>
        </div>
        <ArrowRight className="w-5 h-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-1" />
      </div>
    </Link>
  );
}
