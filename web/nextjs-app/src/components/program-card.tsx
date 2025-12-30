import Link from "next/link";
import Image from "next/image";
import { ExternalLink, Clock, DollarSign, Tag } from "lucide-react";
import type { Program } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ProgramCardProps {
  program: Program;
  className?: string;
}

export function ProgramCard({ program, className }: ProgramCardProps) {
  return (
    <Link
      href={`/programs/${program.slug}`}
      className={cn(
        "block bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow p-4",
        className
      )}
    >
      <div className="flex items-start gap-4">
        {/* Logo */}
        <div className="flex-shrink-0 w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center overflow-hidden">
          {program.logo_url ? (
            <Image
              src={program.logo_url}
              alt={program.name}
              width={48}
              height={48}
              className="object-contain"
            />
          ) : (
            <span className="text-lg font-bold text-gray-400">
              {program.name.charAt(0)}
            </span>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{program.name}</h3>
          {program.domain && (
            <p className="text-sm text-gray-500 truncate">{program.domain}</p>
          )}

          {/* Stats */}
          <div className="mt-2 flex flex-wrap gap-3 text-sm">
            {program.commission_rate && (
              <span className="inline-flex items-center gap-1 text-green-600">
                <DollarSign className="h-3.5 w-3.5" />
                {program.commission_rate}
              </span>
            )}
            {program.cookie_duration_days && (
              <span className="inline-flex items-center gap-1 text-blue-600">
                <Clock className="h-3.5 w-3.5" />
                {program.cookie_duration_days}d cookie
              </span>
            )}
            {program.tracking_platform && (
              <span className="inline-flex items-center gap-1 text-gray-500">
                <Tag className="h-3.5 w-3.5" />
                {program.tracking_platform}
              </span>
            )}
          </div>
        </div>

        {/* Arrow */}
        <ExternalLink className="h-4 w-4 text-gray-400 flex-shrink-0" />
      </div>
    </Link>
  );
}

export function ProgramCardSkeleton() {
  return (
    <div className="bg-white rounded-lg border shadow-sm p-4 animate-pulse">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 bg-gray-200 rounded-lg" />
        <div className="flex-1">
          <div className="h-5 bg-gray-200 rounded w-1/2 mb-2" />
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-3" />
          <div className="flex gap-3">
            <div className="h-4 bg-gray-200 rounded w-16" />
            <div className="h-4 bg-gray-200 rounded w-20" />
          </div>
        </div>
      </div>
    </div>
  );
}
