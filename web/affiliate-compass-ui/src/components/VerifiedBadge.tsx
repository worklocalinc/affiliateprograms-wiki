import { CheckCircle2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface VerifiedBadgeProps {
  date?: string;
  showDate?: boolean;
  className?: string;
}

export function VerifiedBadge({ date, showDate = true, className }: VerifiedBadgeProps) {
  return (
    <Badge variant="verified" className={className}>
      <CheckCircle2 className="w-3 h-3 mr-1" />
      Verified{showDate && date ? ` ${date}` : ""}
    </Badge>
  );
}
