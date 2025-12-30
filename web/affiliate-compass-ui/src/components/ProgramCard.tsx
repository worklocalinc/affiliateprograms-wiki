import { Link } from "react-router-dom";
import { ExternalLink, ArrowRight } from "lucide-react";
import { VerifiedBadge } from "./VerifiedBadge";

interface ProgramCardProps {
  name: string;
  slug: string;
  description: string;
  logo?: string;
  payoutModel: string;
  commission: string;
  cookieLength?: string;
  network?: string;
  verified?: string;
}

export function ProgramCard({
  name,
  slug,
  description,
  logo,
  payoutModel,
  commission,
  cookieLength,
  network,
  verified,
}: ProgramCardProps) {
  return (
    <Link
      to={`/programs/${slug}`}
      className="group block bg-card border border-border rounded-lg p-4 hover:shadow-md hover:border-primary/30 transition-all"
    >
      <div className="flex items-start gap-3">
        {logo ? (
          <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center overflow-hidden shrink-0">
            <img src={logo} alt={name} className="w-8 h-8 object-contain" />
          </div>
        ) : (
          <div className="w-12 h-12 bg-muted rounded-lg flex items-center justify-center shrink-0">
            <span className="text-lg font-semibold text-muted-foreground">{name.charAt(0)}</span>
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors truncate">
              {name}
            </h3>
            <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
          </div>
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{description}</p>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="bg-muted px-2 py-1 rounded">{payoutModel}</span>
            <span className="bg-muted px-2 py-1 rounded">{commission}</span>
            {cookieLength && <span className="bg-muted px-2 py-1 rounded">{cookieLength}</span>}
            {network && <span className="bg-info-bg text-foreground px-2 py-1 rounded">{network}</span>}
          </div>
          {verified && (
            <div className="mt-3">
              <VerifiedBadge date={verified} />
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
