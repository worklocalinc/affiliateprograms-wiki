import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface CitationProps {
  number: number;
  source: string;
  url?: string;
  date?: string;
}

export function Citation({ number, source, url, date }: CitationProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <sup>
          {url ? (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="citation"
            >
              {number}
            </a>
          ) : (
            <span className="citation">{number}</span>
          )}
        </sup>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs">
        <p className="text-sm font-medium">{source}</p>
        {date && <p className="text-xs text-muted-foreground mt-1">Retrieved {date}</p>}
      </TooltipContent>
    </Tooltip>
  );
}

interface SourceListProps {
  sources: {
    id: number;
    source: string;
    url?: string;
    date?: string;
  }[];
}

export function SourceList({ sources }: SourceListProps) {
  return (
    <div className="space-y-2 text-sm">
      {sources.map((source) => (
        <div key={source.id} className="flex gap-3">
          <span className="citation shrink-0">{source.id}</span>
          <div>
            {source.url ? (
              <a href={source.url} target="_blank" rel="noopener noreferrer" className="wiki-link">
                {source.source}
              </a>
            ) : (
              <span>{source.source}</span>
            )}
            {source.date && (
              <span className="text-muted-foreground ml-2">Retrieved {source.date}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
