import { ReactNode } from "react";
import { ExternalLink } from "lucide-react";
import { VerifiedBadge } from "./VerifiedBadge";

interface InfoboxRow {
  label: string;
  value: ReactNode;
}

interface InfoboxProps {
  title: string;
  logo?: string;
  website?: string;
  verified?: string;
  rows: InfoboxRow[];
}

export function Infobox({ title, logo, website, verified, rows }: InfoboxProps) {
  return (
    <div className="infobox">
      {/* Header */}
      <div className="flex items-start gap-4 mb-4 pb-4 border-b border-info-border">
        {logo && (
          <div className="w-16 h-16 bg-card rounded-lg border border-border flex items-center justify-center overflow-hidden shrink-0">
            <img src={logo} alt={title} className="w-12 h-12 object-contain" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <h2 className="font-semibold text-lg text-foreground truncate">{title}</h2>
          {website && (
            <a
              href={website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm wiki-link mt-1"
            >
              {new URL(website).hostname}
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
          {verified && (
            <div className="mt-2">
              <VerifiedBadge date={verified} />
            </div>
          )}
        </div>
      </div>

      {/* Data rows */}
      <dl className="space-y-2">
        {rows.map((row, index) => (
          <div key={index} className="flex gap-3 text-sm">
            <dt className="font-medium text-muted-foreground w-28 shrink-0">{row.label}</dt>
            <dd className="text-foreground">{row.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
